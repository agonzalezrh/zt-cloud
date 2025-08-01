const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 9001;

const CLOUD_PROVIDER = process.env.CLOUD_PROVIDER;
const AWS_ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID || 'Not set';
const AWS_SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY || 'Not set';
const AWS_WEB_CONSOLE_URL = process.env.AWS_WEB_CONSOLE_URL || 'Not set';
const AWS_WEB_CONSOLE_USER_NAME = process.env.AWS_WEB_CONSOLE_USER_NAME || 'Not set';
const AWS_WEB_CONSOLE_PASSWORD = process.env.AWS_WEB_CONSOLE_PASSWORD || 'Not set';
const AWS_SANDBOX_ACCOUNT_ID =  process.env.AWS_SANDBOX_ACCOUNT_ID || 'Not set';
const AWS_ROUTE53_DOMAIN = process.env.AWS_ROUTE53_DOMAIN || 'Not set';
const AWS_DEFAULT_REGION = process.env.AWS_DEFAULT_REGION || 'Not set';



const AZURE_TENANT_ID = process.env.AZURE_TENANT || 'Not set';
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || 'Not set';
const AZURE_PASSWORD = process.env.AZURE_PASSWORD || 'Not set';
const AZURE_SUBSCRIPTION = process.env.AZURE_SUBSCRIPTION || 'No set';
const AZURE_RESOURCEGROUP = process.env.AZURE_RESOURCEGROUP || 'No set';
const AZURE_PASSWORD = process.env.AZURE_PASSWORD || 'Not set';

function generateHtmlContent() {
    let html = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cloud Provider Info</title>
    </head>
    <body>
        <h1>Cloud Provider Information</h1>
        <p><strong>CLOUD_PROVIDER:</strong> ${CLOUD_PROVIDER || 'Not set'}</p>
    `;

    if (CLOUD_PROVIDER === 'aws') {
        html += `
        <h2>AWS Information</h2>
        <img src="aws-logo.svg" alt="AWS Logo" width="150"><br>
        <p><strong>AWS_ACCESS_KEY_ID:</strong> ${AWS_ACCESS_KEY_ID}</p>
        <p><strong>AWS_SECRET_ACCESS_KEY:</strong> ${AWS_SECRET_ACCESS_KEY}</p>
        <p><strong>AWS_ROUTE53_DOMAIN:</strong> ${AWS_ROUTE53_DOMAIN}</p>
        <p><strong>AWS_DEFAULT_REGION:</strong> ${AWS_DEFAULT_REGION}</p>
        <p><strong>AWS_WEB_CONSOLE_URL:</strong> <a href="${AWS_WEB_CONSOLE_URL}" target="_blank">${AWS_WEB_CONSOLE_URL}</a></p>
        <p><strong>AWS_WEB_CONSOLE_USER_NAME:</strong> ${AWS_WEB_CONSOLE_USER_NAME}</p>
        <p><strong>AWS_WEB_CONSOLE_PASSWORD:</strong> ${AWS_WEB_CONSOLE_PASSWORD}</p>
        <p><strong>AWS_SANDBOX_ACCOUNT_ID:</strong> ${AWS_SANDBOX_ACCOUNT_ID}</p>
        `;
    } else if (CLOUD_PROVIDER === 'azure') {
        html += `
        <h2>Azure Information</h2>
        <img src="azure-logo.svg" alt="Azure Logo" width="150"><br>
        <p><strong>AZURE_TENANT_ID:</strong> ${AZURE_TENANT_ID}</p>
        <p><strong>AZURE_CLIENT_ID:</strong> ${AZURE_CLIENT_ID}</p>
        <p><strong>AZURE_PASSSWORD:</strong> ${AZURE_PASSWORD}</p>
        <p><strong>AZURE_SUBSCRIPTION:</strong> ${AZURE_SUBSCRIPTION}</p>
        <p><strong>AZURE_RESOURCEGROUP:</strong> ${AZURE_RESOURCEGROUP}</p>
        `;
    } else {
        html += `
        <p><strong>Note:</strong> CLOUD_PROVIDER environment variable is not set to 'aws' or 'azure'.</p>
        `;
    }

    html += `
    </body>
    </html>
    `;
    return html;
}

const server = http.createServer((req, res) => {
    if (req.url === '/') {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(generateHtmlContent());
   } else if (req.url === '/aws-logo.svg') {
        const svgPath = path.join(__dirname, 'aws-logo.svg');
        fs.readFile(svgPath, (err, data) => {
            if (err) {
                res.writeHead(404, { 'Content-Type': 'text/plain' });
                res.end('SVG not found');
            } else {
                res.writeHead(200, { 'Content-Type': 'image/svg+xml' }); // Crucial Content-Type
                res.end(data);
            }
        });
    } else if (req.url === '/azure-logo.svg') {
        const svgPath = path.join(__dirname, 'azure-logo.svg');
        fs.readFile(svgPath, (err, data) => {
            if (err) {
                res.writeHead(404, { 'Content-Type': 'text/plain' });
                res.end('SVG not found');
            } else {
                res.writeHead(200, { 'Content-Type': 'image/svg+xml' }); // Crucial Content-Type
                res.end(data);
            }
        });
    } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('404 Not Found');
    }
});

server.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
