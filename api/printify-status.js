// Read-only Printify connection status. No orders or charges are created.
module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });
  const token = process.env.PRINTIFY_API_TOKEN;
  if (!token) return res.status(200).json({ connected: false, reason: 'token_not_configured' });
  try {
    const response = await fetch('https://api.printify.com/v1/shops.json', {
      headers: { Authorization: 'Bearer ' + token, Accept: 'application/json' },
      signal: AbortSignal.timeout(8000)
    });
    if (!response.ok) return res.status(200).json({ connected: false, reason: 'authentication_failed' });
    const shops = await response.json();
    return res.status(200).json({ connected: true, shopConfigured: Array.isArray(shops) && shops.length > 0 });
  } catch {
    return res.status(503).json({ connected: false, reason: 'printify_unreachable' });
  }
};
