// Sweeps Titan Stripe Checkout API (Vercel Serverless Function).
// Configure STRIPE_SECRET_KEY, CATALOG_JSON (id -> {price_id,active}),
// and SHIPPING_RATE_ID as Vercel production environment variables.
// Never send secret keys to the browser or commit them to Git.
module.exports = async function handler(req, res) {
  const site = process.env.SITE_ORIGIN || 'https://sweepstitan.com';
  const allowed = [site, 'https://www.sweepstitan.com'];
  const origin = req.headers.origin;
  if (origin && allowed.includes(origin)) res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Vary', 'Origin');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'OPTIONS') return res.status(origin && allowed.includes(origin) ? 204 : 403).end();
  if (req.method !== 'POST') return res.status(405).json({error:'Method not allowed'});
  if (!origin || !allowed.includes(origin)) return res.status(403).json({error:'Origin not allowed'});
  const secret = process.env.STRIPE_SECRET_KEY;
  const shipping = process.env.SHIPPING_RATE_ID;
  const catalogString = process.env.CATALOG_JSON;
  if (!secret || !catalogString || !shipping) return res.status(503).json({error:'Secure checkout is not configured yet'});
  if (!/^sk_(live|test)_/.test(secret) || !/^shr_[A-Za-z0-9]+$/.test(shipping)) return res.status(503).json({error:'Checkout configuration invalid'});
  let catalog;
  try { catalog = JSON.parse(catalogString); } catch { return res.status(503).json({error:'Catalog configuration invalid'}); }
  const cart = req.body?.items;
  if (!Array.isArray(cart) || cart.length < 1 || cart.length > 36) return res.status(400).json({error:'Invalid cart'});
  const quantities = new Map();
  for (const item of cart) {
    if (!item || typeof item.id !== 'string' || !/^st-([1-9]|[12][0-9]|3[0-6])$/.test(item.id) || !Number.isInteger(item.quantity) || item.quantity < 1 || item.quantity > 99) return res.status(400).json({error:'Invalid cart items'});
    const entry = catalog[item.id];
    if (!entry || entry.active !== true || !/^price_[A-Za-z0-9]+$/.test(entry.price_id || '')) return res.status(400).json({error:'Product unavailable: '+item.id});
    quantities.set(item.id, (quantities.get(item.id) || 0) + item.quantity);
    if (quantities.get(item.id) > 99) return res.status(400).json({error:'Quantity limit exceeded'});
  }
  const form = new URLSearchParams();
  form.set('mode','payment');
  form.set('success_url',site+'/shop.html?checkout=success&session_id={CHECKOUT_SESSION_ID}');
  form.set('cancel_url',site+'/shop.html?checkout=cancel');
  form.set('customer_creation','always');
  form.set('billing_address_collection','auto');
  form.set('shipping_address_collection[allowed_countries][0]','US');
  form.set('shipping_options[0][shipping_rate]',shipping);
  form.set('metadata[source]','sweeps-titan-merch');
  let i=0;
  for (const [id,quantity] of quantities) {
    form.set('line_items['+i+'][price]', catalog[id].price_id);
    form.set('line_items['+i+'][quantity]', String(quantity));
    i++;
  }
  try {
    const response = await fetch('https://api.stripe.com/v1/checkout/sessions',{
      method:'POST',
      headers:{Authorization:'Bearer '+secret,'Content-Type':'application/x-www-form-urlencoded'},
      body:form
    });
    const result=await response.json();
    if (!response.ok || typeof result.url !== 'string' || !result.url.startsWith('https://checkout.stripe.com/'))
      return res.status(502).json({error:'Stripe checkout could not be created'});
    return res.status(200).json({url:result.url});
  } catch { return res.status(502).json({error:'Payment provider unavailable'}); }
};
