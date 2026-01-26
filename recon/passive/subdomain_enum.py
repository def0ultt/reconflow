import time
from core.base import BaseModule, Option

class SubdomainEnumModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.meta = {
            'name': 'Passive Subdomain Enumeration',
            'description': 'Enumerate subdomains using passive sources.',
            'author': 'ReconFlow',
            'version': '1.0'
        }
        self.options = {
            'target': Option(name='target', description='Target domain (e.g. example.com)', required=True),
            'verbose': Option(name='verbose', value='false', description='Enable verbose output', required=False)
        }
    
    def run(self, context):
        target = self.options['target'].value
        print(f"🌐 Finding subdomains for {target}...")
        if self.options['verbose'].value.lower() == 'true':
            print("Verbose mode enabled.")
            
        # Simulated work
        time.sleep(1)
        results = [f"www.{target}", f"api.{target}", f"dev.{target}"]
        for sub in results:
            print(f"  - {sub}")
        return results

# For compatibility during migration, we can keep the old function or remove it.
# Removing it to force usage of module system.
