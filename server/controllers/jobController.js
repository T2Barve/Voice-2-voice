import axios from 'axios';

/**
 * Proxy controller for Adzuna Job Search API
 * This keeps the API keys on the server and allows us to pre-process requests.
 */
export const searchJobs = async (req, res) => {
    try {
        // We extract search parameters from query string
        // 'what' -> role
        // 'where' -> location
        // 'country' -> defaults to 'in' (India) based on user's timezone, or 'gb' as per doc example
        const { role, location, country = 'in', permanent, contract } = req.query;
        
        const appId = process.env.ADZUNA_APP_ID;
        const appKey = process.env.ADZUNA_APP_KEY;

        if (!appId || !appKey) {
            return res.status(500).json({ error: 'Adzuna API credentials not configured on server' });
        }

        // Adzuna Search Endpoint: https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
        // Parameters: what (role), where (location), results_per_page, sort_by
        let url = `https://api.adzuna.com/v1/api/jobs/${country}/search/1?app_id=${appId}&app_key=${appKey}&results_per_page=25&sort_by=date`;
        
        if (permanent === '1') url += `&permanent=1`;
        if (contract === '1') url += `&contract=1`;
        
        if (role) {
            url += `&what=${encodeURIComponent(role)}`;
        }
        
        if (location) {
            url += `&where=${encodeURIComponent(location)}`;
        }

        console.log(`[JobSearch] Querying Adzuna: ${role} in ${location} (${country})`);

        const response = await axios.get(url);
        
        // Adzuna returns results in response.data.results
        res.status(200).json({
            success: true,
            results: response.data.results
        });
    } catch (error) {
        console.error('Adzuna API Error:', error.response?.data || error.message);
        res.status(500).json({ 
            success: false, 
            message: 'Failed to fetch job listings from Adzuna',
            error: error.message 
        });
    }
};
