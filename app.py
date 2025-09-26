import os
from flask import Flask, render_template_string, send_file, abort, jsonify
import subprocess
import sys

app = Flask(__name__)

# Environment variables
PORT = int(os.environ.get('PORT', 9001))
CLOUD_PROVIDER = os.environ.get('CLOUD_PROVIDER')

# AWS Environment variables
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'Not set')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'Not set')
AWS_WEB_CONSOLE_URL = os.environ.get('AWS_WEB_CONSOLE_URL', 'Not set')
AWS_WEB_CONSOLE_USER_NAME = os.environ.get('AWS_WEB_CONSOLE_USER_NAME', 'Not set')
AWS_WEB_CONSOLE_PASSWORD = os.environ.get('AWS_WEB_CONSOLE_PASSWORD', 'Not set')
AWS_SANDBOX_ACCOUNT_ID = os.environ.get('AWS_SANDBOX_ACCOUNT_ID', 'Not set')
AWS_ROUTE53_DOMAIN = os.environ.get('AWS_ROUTE53_DOMAIN', 'Not set')
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', 'Not set')

# Azure Environment variables
AZURE_TENANT_ID = os.environ.get('AZURE_TENANT', 'Not set')
AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', 'Not set')
AZURE_PASSWORD = os.environ.get('AZURE_PASSWORD', 'Not set')
AZURE_SUBSCRIPTION = os.environ.get('AZURE_SUBSCRIPTION', 'Not set')
AZURE_RESOURCEGROUP = os.environ.get('AZURE_RESOURCEGROUP', 'Not set')

def perform_azure_login():
    """Perform Azure CLI login using service principal"""
    try:
        # Check if Azure CLI is available
        result = subprocess.run(['az', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Azure CLI not found or not working", file=sys.stderr)
            return False
        
        # Perform login
        login_cmd = [
            'az', 'login', '--service-principal',
            '-u', AZURE_CLIENT_ID,
            '-p', AZURE_PASSWORD,
            '--tenant', AZURE_TENANT_ID
        ]
        
        result = subprocess.run(login_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Azure CLI login successful")
            return True
        else:
            print(f"Azure CLI login failed: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error during Azure CLI login: {e}", file=sys.stderr)
        return False

def generate_azure_diagram():
    """Generate Azure resource information with simple diagram"""
    try:
        # Get Azure resources using Azure CLI
        result = subprocess.run([
            'az', 'resource', 'list', 
            '--output', 'table',
            '--query', '[].{Name:name, Type:type, ResourceGroup:resourceGroup, Location:location}'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Parse resources and create both table and diagram
            resources_text = result.stdout
            table_html = create_azure_resources_html(resources_text)
            diagram_html = create_azure_diagram_svg(resources_text)
            return f"{diagram_html}{table_html}"
        else:
            print(f"Azure CLI resource list failed: {result.stderr}", file=sys.stderr)
            return create_azure_fallback_html()
            
    except subprocess.TimeoutExpired:
        print("Azure CLI command timed out", file=sys.stderr)
        return create_azure_fallback_html()
    except Exception as e:
        print(f"Error generating Azure resource info: {e}", file=sys.stderr)
        return create_azure_fallback_html()

def create_azure_diagram_svg(resources_text):
    """Create a responsive SVG diagram of Azure resources"""
    lines = resources_text.strip().split('\n')
    if len(lines) < 3:
        return ""
    
    # Parse resources
    resource_lines = lines[2:]  # Skip header and separator
    resources = []
    
    for line in resource_lines:
        if line.strip():
            cells = [cell.strip() for cell in line.split('  ') if cell.strip()]
            if len(cells) >= 4:  # Name, Type, ResourceGroup, Location
                resources.append({
                    'name': cells[0],
                    'type': cells[1],
                    'resourceGroup': cells[2],
                    'location': cells[3]
                })
    
    if not resources:
        return ""
    
    # Group resources by resource group
    resource_groups = {}
    for resource in resources:
        rg = resource['resourceGroup']
        if rg not in resource_groups:
            resource_groups[rg] = []
        resource_groups[rg].append(resource)
    
    # Create responsive SVG with JavaScript
    svg_id = f"azure-diagram-{hash(str(resources)) % 10000}"
    
    svg_html = f'''
    <div style="margin: 20px 0; text-align: center;">
        <div id="{svg_id}-container" style="width: 100%; height: 500px; border: 1px solid #ddd; background: #fafafa; overflow: auto;">
            <svg id="{svg_id}" width="100%" height="100%" viewBox="0 0 1200 600" preserveAspectRatio="none">
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="#1976d2" />
                    </marker>
                </defs>
                <text x="500" y="25" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#333">Azure Resources Overview</text>
    '''
    
    # Calculate layout
    num_rgs = len(resource_groups)
    if num_rgs == 0:
        return ""
    
    # Draw resource groups
    x_spacing = 800 // num_rgs if num_rgs > 0 else 400
    y_start = 60
    
    for i, (rg_name, rg_resources) in enumerate(resource_groups.items()):
        x = 100 + i * x_spacing
        
        # Resource group container (reduced by 25% from 240px to 180px)
        container_height = max(120, len(rg_resources) * 80 + 40)
        svg_html += f'<rect x="{x-90}" y="{y_start-20}" width="180" height="{container_height}" fill="#e3f2fd" stroke="#1976d2" stroke-width="2" rx="5"/>'
        
        # Resource group title (truncated if too long)
        display_rg_name = truncate_text(rg_name, 30)
        svg_html += f'<text x="{x}" y="{y_start-5}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1976d2">{display_rg_name}</text>'
        
        # Resources in this group
        for j, resource in enumerate(rg_resources):
            y = y_start + j * 80
            
            # Resource icon (adjusted for smaller box)
            icon = get_azure_icon(resource['type'])
            svg_html += f'<circle cx="{x-45}" cy="{y+10}" r="12" fill="#1976d2"/>'
            svg_html += f'<text x="{x-45}" y="{y+15}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="white">{icon}</text>'
            
            # Resource name (truncated) with hover tooltip
            display_name = truncate_text(resource['name'], 20)
            svg_html += f'<text x="{x-20}" y="{y+8}" font-family="Arial, sans-serif" font-size="10" fill="#333" title="{resource["name"]}">{display_name}</text>'
            
            # Resource type (truncated) with hover tooltip
            resource_type = resource['type'].split('/')[-1]
            display_type = truncate_text(resource_type, 20)
            svg_html += f'<text x="{x-20}" y="{y+20}" font-family="Arial, sans-serif" font-size="8" fill="#666" title="{resource_type}">{display_type}</text>'
            
            # Add arrow to next resource (if not the last one)
            if j < len(rg_resources) - 1:
                arrow_y = y + 35
                svg_html += f'<line x1="{x-45}" y1="{arrow_y}" x2="{x-45}" y2="{arrow_y + 20}" stroke="#1976d2" stroke-width="2" marker-end="url(#arrowhead)"/>'
    
    svg_html += '''
            </svg>
        </div>
    </div>
    
    <script>
        function resizeDiagram() {
            const container = document.getElementById('{svg_id}-container');
            const svg = document.getElementById('{svg_id}');
            if (container && svg) {
                // Calculate content dimensions based on number of resource groups
                const numResourceGroups = {len(resource_groups)};
                const contentWidth = Math.max(1200, numResourceGroups * 250);
                const contentHeight = Math.max(600, 500);
                
                // Set SVG dimensions to content size for proper scrolling
                svg.setAttribute('width', contentWidth);
                svg.setAttribute('height', contentHeight);
                svg.setAttribute('viewBox', `0 0 ${{contentWidth}} ${{contentHeight}}`);
            }
        }
        
        // Resize on window resize
        window.addEventListener('resize', resizeDiagram);
        
        // Initial resize
        setTimeout(resizeDiagram, 100);
    </script>
    '''
    
    return svg_html

def truncate_text(text, max_length):
    """Truncate text to max_length and add ellipsis if needed"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def get_azure_icon(resource_type):
    """Get a simple icon character for Azure resource type"""
    type_lower = resource_type.lower()
    
    if 'virtualmachine' in type_lower or 'vm' in type_lower:
        return '🖥'
    elif 'storage' in type_lower:
        return '💾'
    elif 'network' in type_lower or 'vnet' in type_lower:
        return '🌐'
    elif 'database' in type_lower or 'sql' in type_lower:
        return '🗄'
    elif 'app' in type_lower or 'function' in type_lower:
        return '⚡'
    elif 'keyvault' in type_lower:
        return '🔐'
    elif 'loadbalancer' in type_lower:
        return '⚖'
    elif 'disk' in type_lower:
        return '💿'
    elif 'container' in type_lower or 'aks' in type_lower:
        return '📦'
    else:
        return '☁'

def create_azure_resources_html(resources_text):
    """Create HTML representation of Azure resources"""
    lines = resources_text.strip().split('\n')
    if len(lines) < 3:  # Header + separator + at least one resource
        return create_azure_fallback_html()
    
    # Parse the table output
    header_line = lines[0]
    separator_line = lines[1]
    resource_lines = lines[2:]
    
    # Extract column names from header
    columns = [col.strip() for col in header_line.split('  ') if col.strip()]
    
    html = """
    <div style="margin-top: 20px;">
        <h4 style="margin-bottom: 10px; color: #333;">Detailed Resource List</h4>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-family: monospace; font-size: 12px;">
                <thead>
                    <tr style="background: #e1e1e1;">
    """
    
    # Add header
    for col in columns:
        html += f'<th style="padding: 8px; border: 1px solid #ccc; text-align: left;">{col}</th>'
    
    html += """
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add resource rows
    for line in resource_lines:
        if line.strip():
            cells = [cell.strip() for cell in line.split('  ') if cell.strip()]
            if len(cells) >= len(columns):
                html += '<tr>'
                for cell in cells[:len(columns)]:
                    html += f'<td style="padding: 6px; border: 1px solid #ccc;">{cell}</td>'
                html += '</tr>'
    
    html += """
                </tbody>
            </table>
        </div>
    </div>
    """
    
    return html

def create_azure_fallback_html():
    """Create fallback HTML when Azure CLI fails"""
    return """
    <div style="padding: 20px; text-align: center; color: #666;">
        <p><strong>Unable to retrieve Azure resources</strong></p>
        <p>This could be due to:</p>
        <ul style="text-align: left; display: inline-block;">
            <li>Azure CLI authentication issues</li>
            <li>Insufficient permissions</li>
            <li>Network connectivity problems</li>
            <li>No resources found in the subscription</li>
        </ul>
    </div>
    """

def get_azure_diagram_html():
    """Generate HTML for Azure resources with loading state"""
    return """
    <div id="azure-resources-container" style="margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h3 style="margin: 0; color: #333;">Azure Resources Overview</h3>
            <button id="refresh-azure-btn" onclick="refreshAzureResources()" 
                    style="padding: 8px 16px; background: #0078d4; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                🔄 Refresh
            </button>
        </div>
        <div id="azure-loading" style="text-align: center; padding: 40px; color: #666;">
            <div style="font-size: 18px; margin-bottom: 10px;">⏳</div>
            <p>Loading Azure resources...</p>
        </div>
        <div id="azure-content" style="display: none;"></div>
    </div>
    <script>
        // Load Azure resources on page load
        document.addEventListener('DOMContentLoaded', function() {
            refreshAzureResources();
        });
        
        function refreshAzureResources() {
            const loadingDiv = document.getElementById('azure-loading');
            const contentDiv = document.getElementById('azure-content');
            const refreshBtn = document.getElementById('refresh-azure-btn');
            
            // Show loading state
            loadingDiv.style.display = 'block';
            contentDiv.style.display = 'none';
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '⏳ Loading...';
            
            // Fetch Azure resources
            fetch('api/azure-resources')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        contentDiv.innerHTML = data.html;
                        contentDiv.style.display = 'block';
                        loadingDiv.style.display = 'none';
                    } else {
                        contentDiv.innerHTML = data.html;
                        contentDiv.style.display = 'block';
                        loadingDiv.style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Error fetching Azure resources:', error);
                    contentDiv.innerHTML = '<div style="padding: 20px; text-align: center; color: red;"><p>Error loading Azure resources. Please try again.</p></div>';
                    contentDiv.style.display = 'block';
                    loadingDiv.style.display = 'none';
                })
                .finally(() => {
                    refreshBtn.disabled = false;
                    refreshBtn.innerHTML = '🔄 Refresh';
                });
        }
    </script>
    """

def generate_html_content():
    """Generate HTML content for the main page"""
    if CLOUD_PROVIDER == 'aws_and_azure':
        return generate_tabbed_html()
    else:
        return generate_single_provider_html()

def generate_tabbed_html():
    """Generate HTML with tabs for AWS and Azure"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cloud Provider Info</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            .tab-container {{ margin-top: 20px; }}
            .tab-buttons {{ display: flex; border-bottom: 2px solid #ddd; }}
            .tab-button {{ 
                background: #f1f1f1; 
                border: none; 
                padding: 15px 25px; 
                cursor: pointer; 
                font-size: 16px;
                border-radius: 5px 5px 0 0;
                margin-right: 5px;
            }}
            .tab-button.active {{ 
                background: #fff; 
                border-bottom: 2px solid #fff;
                color: #333;
            }}
            .tab-button:hover {{ background: #e1e1e1; }}
            .tab-content {{ 
                display: none; 
                padding: 20px; 
                border: 1px solid #ddd; 
                border-top: none; 
                background: #fff;
            }}
            .tab-content.active {{ display: block; }}
            .provider-info {{ margin: 20px 0; }}
            .provider-info h2 {{ color: #333; margin-bottom: 15px; }}
            .provider-info p {{ margin: 10px 0; }}
            .provider-info img {{ margin: 10px 0; }}
            .provider-info a {{ color: #0066cc; }}
            .diagram-container {{ margin: 20px 0; text-align: center; }}
            .diagram-container img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <h1>Cloud Provider Information</h1>
        <p><strong>CLOUD_PROVIDER:</strong> {CLOUD_PROVIDER or 'Not set'}</p>
        
        <div class="tab-container">
            <div class="tab-buttons">
                <button class="tab-button active" onclick="showTab('aws')">AWS</button>
                <button class="tab-button" onclick="showTab('azure')">Azure</button>
            </div>
            
            <div id="aws" class="tab-content active">
                <div class="provider-info">
                    <h2>AWS Information</h2>
                    <img src="aws-logo.svg" alt="AWS Logo" width="150"><br>
                    <p><strong>AWS_ACCESS_KEY_ID:</strong> {AWS_ACCESS_KEY_ID}</p>
                    <p><strong>AWS_SECRET_ACCESS_KEY:</strong> {AWS_SECRET_ACCESS_KEY}</p>
                    <p><strong>AWS_ROUTE53_DOMAIN:</strong> {AWS_ROUTE53_DOMAIN}</p>
                    <p><strong>AWS_DEFAULT_REGION:</strong> {AWS_DEFAULT_REGION}</p>
                    <p><strong>AWS_WEB_CONSOLE_URL:</strong> <a href="{AWS_WEB_CONSOLE_URL}" target="_blank">{AWS_WEB_CONSOLE_URL}</a></p>
                    <p><strong>AWS_WEB_CONSOLE_USER_NAME:</strong> {AWS_WEB_CONSOLE_USER_NAME}</p>
                    <p><strong>AWS_WEB_CONSOLE_PASSWORD:</strong> {AWS_WEB_CONSOLE_PASSWORD}</p>
                    <p><strong>AWS_SANDBOX_ACCOUNT_ID:</strong> {AWS_SANDBOX_ACCOUNT_ID}</p>
                </div>
            </div>
            
            <div id="azure" class="tab-content">
                <div class="provider-info">
                    <h2>Azure Resource Topology</h2>
                    <img src="azure-logo.svg" alt="Azure Logo" width="150"><br>
                    
                    <!-- Collapsible Credentials Section -->
                    <div style="margin: 20px 0;">
                        <button onclick="toggleCredentials()" style="
                            background: #f1f1f1; 
                            border: 1px solid #ddd; 
                            padding: 10px 15px; 
                            cursor: pointer; 
                            border-radius: 4px;
                            font-size: 14px;
                            width: 100%;
                            text-align: left;
                        ">
                            <span id="credentials-toggle">▼</span> Show credentials
                        </button>
                        <div id="credentials-content" style="display: none; margin-top: 10px; padding: 15px; background: #f9f9f9; border: 1px solid #ddd; border-radius: 4px;">
                            <h4 style="margin-top: 0; color: #333;">Azure Credentials</h4>
                            <p><strong>AZURE_TENANT_ID:</strong> {AZURE_TENANT_ID}</p>
                            <p><strong>AZURE_CLIENT_ID:</strong> {AZURE_CLIENT_ID}</p>
                            <p><strong>AZURE_PASSWORD:</strong> {AZURE_PASSWORD}</p>
                            <p><strong>AZURE_SUBSCRIPTION:</strong> {AZURE_SUBSCRIPTION}</p>
                            <p><strong>AZURE_RESOURCEGROUP:</strong> {AZURE_RESOURCEGROUP}</p>
                        </div>
                    </div>
                    
                    <div class="diagram-container">
                        {get_azure_diagram_html()}
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function showTab(tabName) {{
                // Hide all tab contents
                var contents = document.getElementsByClassName('tab-content');
                for (var i = 0; i < contents.length; i++) {{
                    contents[i].classList.remove('active');
                }}
                
                // Remove active class from all buttons
                var buttons = document.getElementsByClassName('tab-button');
                for (var i = 0; i < buttons.length; i++) {{
                    buttons[i].classList.remove('active');
                }}
                
                // Show selected tab content
                document.getElementById(tabName).classList.add('active');
                
                // Add active class to clicked button
                event.target.classList.add('active');
            }}
            
            function toggleCredentials() {{
                var content = document.getElementById('credentials-content');
                var toggle = document.getElementById('credentials-toggle');
                var button = event.target;
                
                if (content.style.display === 'none') {{
                    content.style.display = 'block';
                    toggle.textContent = '▲';
                    button.innerHTML = '<span id="credentials-toggle">▲</span> Hide credentials';
                }} else {{
                    content.style.display = 'none';
                    toggle.textContent = '▼';
                    button.innerHTML = '<span id="credentials-toggle">▼</span> Show credentials';
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html

def generate_single_provider_html():
    """Generate HTML for single provider (AWS or Azure only)"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cloud Provider Info</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1, h2 {{ color: #333; }}
            p {{ margin: 10px 0; }}
            img {{ margin: 10px 0; }}
            a {{ color: #0066cc; }}
            .diagram-container {{ margin: 20px 0; text-align: center; }}
            .diagram-container img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <h1>Cloud Provider Information</h1>
        <p><strong>CLOUD_PROVIDER:</strong> {CLOUD_PROVIDER or 'Not set'}</p>
    """
    
    if CLOUD_PROVIDER == 'aws':
        html += f"""
        <h2>AWS Information</h2>
        <img src="aws-logo.svg" alt="AWS Logo" width="150"><br>
        <p><strong>AWS_ACCESS_KEY_ID:</strong> {AWS_ACCESS_KEY_ID}</p>
        <p><strong>AWS_SECRET_ACCESS_KEY:</strong> {AWS_SECRET_ACCESS_KEY}</p>
        <p><strong>AWS_ROUTE53_DOMAIN:</strong> {AWS_ROUTE53_DOMAIN}</p>
        <p><strong>AWS_DEFAULT_REGION:</strong> {AWS_DEFAULT_REGION}</p>
        <p><strong>AWS_WEB_CONSOLE_URL:</strong> <a href="{AWS_WEB_CONSOLE_URL}" target="_blank">{AWS_WEB_CONSOLE_URL}</a></p>
        <p><strong>AWS_WEB_CONSOLE_USER_NAME:</strong> {AWS_WEB_CONSOLE_USER_NAME}</p>
        <p><strong>AWS_WEB_CONSOLE_PASSWORD:</strong> {AWS_WEB_CONSOLE_PASSWORD}</p>
        <p><strong>AWS_SANDBOX_ACCOUNT_ID:</strong> {AWS_SANDBOX_ACCOUNT_ID}</p>
        """
    elif CLOUD_PROVIDER == 'azure':
        html += f"""
        <h2>Azure Resource Topology</h2>
        <img src="azure-logo.svg" alt="Azure Logo" width="150"><br>
        
        <!-- Collapsible Credentials Section -->
        <div style="margin: 20px 0;">
            <button onclick="toggleCredentials()" style="
                background: #f1f1f1; 
                border: 1px solid #ddd; 
                padding: 10px 15px; 
                cursor: pointer; 
                border-radius: 4px;
                font-size: 14px;
                width: 100%;
                text-align: left;
            ">
                <span id="credentials-toggle">▼</span> Show credentials
            </button>
            <div id="credentials-content" style="display: none; margin-top: 10px; padding: 15px; background: #f9f9f9; border: 1px solid #ddd; border-radius: 4px;">
                <h4 style="margin-top: 0; color: #333;">Azure Credentials</h4>
                <p><strong>AZURE_TENANT_ID:</strong> {AZURE_TENANT_ID}</p>
                <p><strong>AZURE_CLIENT_ID:</strong> {AZURE_CLIENT_ID}</p>
                <p><strong>AZURE_PASSWORD:</strong> {AZURE_PASSWORD}</p>
                <p><strong>AZURE_SUBSCRIPTION:</strong> {AZURE_SUBSCRIPTION}</p>
                <p><strong>AZURE_RESOURCEGROUP:</strong> {AZURE_RESOURCEGROUP}</p>
            </div>
        </div>
        
        <div class="diagram-container">
            {get_azure_diagram_html()}
        </div>
        """
    else:
        html += """
        <p><strong>Note:</strong> CLOUD_PROVIDER environment variable is not set to 'aws' or 'azure'.</p>
        """
    
    html += """
    <script>
        function toggleCredentials() {
            var content = document.getElementById('credentials-content');
            var toggle = document.getElementById('credentials-toggle');
            var button = event.target;
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                toggle.textContent = '▲';
                button.innerHTML = '<span id="credentials-toggle">▲</span> Hide credentials';
            } else {
                content.style.display = 'none';
                toggle.textContent = '▼';
                button.innerHTML = '<span id="credentials-toggle">▼</span> Show credentials';
            }
        }
    </script>
    </body>
    </html>
    """
    return html

@app.route('/')
def index():
    """Main page route"""
    return render_template_string(generate_html_content())

@app.route('/aws-logo.svg')
def aws_logo():
    """Serve AWS logo"""
    try:
        return send_file('aws-logo.svg', mimetype='image/svg+xml')
    except FileNotFoundError:
        abort(404)

@app.route('/azure-logo.svg')
def azure_logo():
    """Serve Azure logo"""
    try:
        return send_file('azure-logo.svg', mimetype='image/svg+xml')
    except FileNotFoundError:
        abort(404)

@app.route('/api/azure-resources')
def azure_resources_api():
    """API endpoint to get Azure resources asynchronously"""
    try:
        html_content = generate_azure_diagram()
        return jsonify({
            'success': True,
            'html': html_content
        })
    except Exception as e:
        print(f"Error in Azure resources API: {e}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': str(e),
            'html': create_azure_fallback_html()
        })

if __name__ == '__main__':
    # Perform Azure login on startup if Azure credentials are provided
    if CLOUD_PROVIDER in ['azure', 'aws_and_azure'] and AZURE_CLIENT_ID != 'Not set':
        print("Attempting Azure CLI login...")
        perform_azure_login()
    
    app.run(host='0.0.0.0', port=PORT, debug=False)