// Cloudflare Pages Function — POST /api/quote
// Creates an Odoo CRM lead for the R Brothers factory site and optionally
// notifies n8n after successful creation.

export async function onRequestPost(context) {
  const { request, env } = context;

  try {
    const body = await request.json();
    const {
      name,
      email,
      phone,
      service,
      address,
      preferred_date,
      message,
      sms_consent,
      utm_source,
      utm_medium,
      utm_campaign,
    } = body;

    if (!name || !service) {
      return Response.json(
        { success: false, error: 'Name and service are required.' },
        { status: 400, headers: CORS_HEADERS }
      );
    }

    const siteName = env.SITE_NAME || 'R Brothers Website';
    const descLines = [
      `Service Requested: ${service}`,
      `Source: ${utm_source || siteName}`,
    ];
    if (utm_medium) descLines.push(`Medium: ${utm_medium}`);
    if (utm_campaign) descLines.push(`Campaign: ${utm_campaign}`);
    if (phone) descLines.push(`Phone: ${phone}`);
    if (email) descLines.push(`Email: ${email}`);
    if (address) descLines.push(`Address: ${address}`);
    if (preferred_date) descLines.push(`Preferred Date: ${preferred_date}`);
    if (message) descLines.push(`Notes: ${message}`);
    if (sms_consent) descLines.push('SMS Consent: Yes');
    const description = descLines.join('<br/>');

    const authResp = await fetch(`${env.ODOO_URL}/xmlrpc/2/common`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: xmlrpcCall('authenticate', [env.ODOO_DB, env.ODOO_USERNAME, env.ODOO_API_KEY, {}]),
    });
    const uid = parseXmlrpcResponse(await authResp.text());
    if (!uid) throw new Error('Odoo authentication failed');

    const leadVals = {
      name: `${service} - ${name} (${siteName})`,
      contact_name: name,
      email_from: email || false,
      phone: phone || false,
      street: address || false,
      description,
      type: 'opportunity',
    };

    if (utm_source) {
      const srcId = await getOrCreateUtmRecord(env, uid, 'utm.source', utm_source);
      if (srcId) leadVals.source_id = srcId;
    }
    if (utm_medium) {
      const medId = await getOrCreateUtmRecord(env, uid, 'utm.medium', utm_medium);
      if (medId) leadVals.medium_id = medId;
    }
    if (utm_campaign) {
      const campId = await getOrCreateUtmRecord(env, uid, 'utm.campaign', utm_campaign);
      if (campId) leadVals.campaign_id = campId;
    }

    const createResp = await fetch(`${env.ODOO_URL}/xmlrpc/2/object`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: xmlrpcCall('execute_kw', [
        env.ODOO_DB,
        uid,
        env.ODOO_API_KEY,
        'crm.lead',
        'create',
        [leadVals],
      ]),
    });
    const leadId = parseXmlrpcResponse(await createResp.text());
    if (!leadId) throw new Error('Lead creation returned no ID');

    if (env.N8N_RBROS_LEAD_WEBHOOK_URL) {
      context.waitUntil(notifyN8n(env.N8N_RBROS_LEAD_WEBHOOK_URL, {
        name,
        service,
        phone: phone || '',
        email: email || '',
        city: 'Edison',
        lead_id: leadId,
        site_name: siteName,
      }));
    }

    return Response.json(
      { success: true, lead_id: leadId, message: "Thanks! We'll be in touch shortly." },
      { headers: CORS_HEADERS }
    );
  } catch (err) {
    console.error('Lead form error:', err);
    return Response.json(
      { success: false, error: 'Submission failed. Please call or email us directly.' },
      { status: 500, headers: CORS_HEADERS }
    );
  }
}

export async function onRequestOptions() {
  return new Response(null, { headers: CORS_HEADERS });
}

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

async function notifyN8n(url, payload) {
  try {
    await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } catch (err) {
    console.error('n8n notify failed:', err);
  }
}

async function getOrCreateUtmRecord(env, uid, model, name) {
  try {
    const searchResp = await fetch(`${env.ODOO_URL}/xmlrpc/2/object`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: xmlrpcCall('execute_kw', [
        env.ODOO_DB,
        uid,
        env.ODOO_API_KEY,
        model,
        'search_read',
        [[[['name', '=', name]]]],
        { fields: ['id'], limit: 1 },
      ]),
    });
    const records = parseXmlrpcList(await searchResp.text());
    if (records && records.length > 0) return records[0];

    const createResp = await fetch(`${env.ODOO_URL}/xmlrpc/2/object`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/xml' },
      body: xmlrpcCall('execute_kw', [
        env.ODOO_DB,
        uid,
        env.ODOO_API_KEY,
        model,
        'create',
        [{ name }],
      ]),
    });
    return parseXmlrpcResponse(await createResp.text());
  } catch (_) {
    return null;
  }
}

function parseXmlrpcList(xml) {
  const ids = [];
  const matches = xml.matchAll(/<int>(\d+)<\/int>/g);
  for (const m of matches) ids.push(parseInt(m[1], 10));
  return ids;
}

function xmlrpcCall(method, params) {
  const paramsXml = params.map((p) => `<param><value>${valueToXml(p)}</value></param>`).join('');
  return `<?xml version="1.0"?><methodCall><methodName>${method}</methodName><params>${paramsXml}</params></methodCall>`;
}

function valueToXml(value) {
  if (value === null || value === false) return '<boolean>0</boolean>';
  if (value === true) return '<boolean>1</boolean>';
  if (typeof value === 'number') return `<int>${value}</int>`;
  if (typeof value === 'string') return `<string>${escapeXml(value)}</string>`;
  if (Array.isArray(value)) {
    return `<array><data>${value.map((v) => `<value>${valueToXml(v)}</value>`).join('')}</data></array>`;
  }
  if (typeof value === 'object') {
    const members = Object.entries(value)
      .map(([k, v]) => `<member><name>${k}</name><value>${valueToXml(v)}</value></member>`)
      .join('');
    return `<struct>${members}</struct>`;
  }
  return `<string>${escapeXml(String(value))}</string>`;
}

function escapeXml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function parseXmlrpcResponse(xml) {
  if (xml.includes('<fault>')) {
    const m = xml.match(/<string>(.*?)<\/string>/);
    throw new Error(`Odoo fault: ${m ? m[1] : 'unknown'}`);
  }
  const intMatch = xml.match(/<int>(\d+)<\/int>/);
  if (intMatch) return parseInt(intMatch[1], 10);
  const i4Match = xml.match(/<i4>(\d+)<\/i4>/);
  if (i4Match) return parseInt(i4Match[1], 10);
  const strMatch = xml.match(/<string>(.*?)<\/string>/);
  if (strMatch) return strMatch[1];
  const boolMatch = xml.match(/<boolean>([01])<\/boolean>/);
  if (boolMatch) return boolMatch[1] === '1';
  return null;
}
