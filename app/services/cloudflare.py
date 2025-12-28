"""Cloudflare API service for DNS management."""
import httpx
import logging
from typing import Optional, Dict, List
from app.core.config import settings

logger = logging.getLogger(__name__)

# Cloudflare API base URL
CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"


class CloudflareAPIError(Exception):
    """Custom exception for Cloudflare API errors."""
    pass


class CloudflareService:
    """Service for managing Cloudflare DNS via API."""
    
    def __init__(self, api_token: Optional[str] = None, account_id: Optional[str] = None):
        """
        Initialize Cloudflare service.
        
        Args:
            api_token: Cloudflare API token (from settings if not provided)
            account_id: Cloudflare account ID (from settings if not provided)
        """
        self.api_token = api_token or settings.CLOUDFLARE_API_TOKEN
        self.account_id = account_id or settings.CLOUDFLARE_ACCOUNT_ID
        
        if not self.api_token:
            raise ValueError("Cloudflare API token is required")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Make HTTP request to Cloudflare API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            
        Returns:
            API response as dictionary
            
        Raises:
            CloudflareAPIError: If API request fails
        """
        url = f"{CLOUDFLARE_API_BASE}/{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data if data else None
                )
                response.raise_for_status()
                result = response.json()
                
                # Check Cloudflare API result
                if not result.get("success", False):
                    errors = result.get("errors", [])
                    error_msg = "; ".join([e.get("message", "Unknown error") for e in errors])
                    raise CloudflareAPIError(f"Cloudflare API error: {error_msg}")
                
                return result
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Cloudflare API HTTP error: {error_msg}")
            raise CloudflareAPIError(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Cloudflare API request error: {error_msg}")
            raise CloudflareAPIError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Cloudflare API unexpected error: {error_msg}")
            raise CloudflareAPIError(error_msg)
    
    async def get_zone(self, domain: str) -> Optional[Dict]:
        """
        Get zone information for a domain.
        
        Args:
            domain: Domain name (e.g., "example.com")
            
        Returns:
            Zone information dict or None if not found
        """
        try:
            result = await self._make_request("GET", f"zones?name={domain}")
            zones = result.get("result", [])
            return zones[0] if zones else None
        except CloudflareAPIError:
            return None
    
    async def create_zone(self, domain: str) -> Dict:
        """
        Create a new zone (add domain to Cloudflare).
        
        Args:
            domain: Domain name (e.g., "example.com")
            
        Returns:
            Zone information dict
        """
        if not self.account_id:
            raise ValueError("Cloudflare account ID is required to create zones")
        
        data = {
            "name": domain,
            "account": {"id": self.account_id},
            "type": "full"  # Full DNS setup
        }
        
        result = await self._make_request("POST", "zones", data)
        zone = result.get("result", {})
        logger.info(f"Created Cloudflare zone for {domain}: {zone.get('id')}")
        return zone
    
    async def get_or_create_zone(self, domain: str) -> Dict:
        """
        Get existing zone or create new one.
        
        Args:
            domain: Domain name
            
        Returns:
            Zone information dict
        """
        zone = await self.get_zone(domain)
        if zone:
            logger.info(f"Zone already exists for {domain}: {zone.get('id')}")
            return zone
        
        return await self.create_zone(domain)
    
    async def create_dns_record(
        self, 
        zone_id: str, 
        record_type: str, 
        name: str, 
        content: str,
        ttl: int = 3600,
        priority: Optional[int] = None
    ) -> Dict:
        """
        Create a DNS record.
        
        Args:
            zone_id: Cloudflare zone ID
            record_type: DNS record type (A, AAAA, CNAME, MX, TXT, etc.)
            name: Record name (use "@" for root domain)
            content: Record content (IP address, domain, etc.)
            ttl: Time to live in seconds (default: 3600)
            priority: Priority for MX records
            
        Returns:
            Created DNS record dict
        """
        data = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": ttl
        }
        
        if priority is not None:
            data["priority"] = priority
        
        result = await self._make_request(
            "POST", 
            f"zones/{zone_id}/dns_records", 
            data
        )
        record = result.get("result", {})
        logger.info(f"Created {record_type} record for {name}: {content}")
        return record
    
    async def list_dns_records(self, zone_id: str, record_type: Optional[str] = None) -> List[Dict]:
        """
        List DNS records for a zone.
        
        Args:
            zone_id: Cloudflare zone ID
            record_type: Optional filter by record type
            
        Returns:
            List of DNS record dicts
        """
        endpoint = f"zones/{zone_id}/dns_records"
        if record_type:
            endpoint += f"?type={record_type}"
        
        result = await self._make_request("GET", endpoint)
        return result.get("result", [])
    
    async def delete_dns_record(self, zone_id: str, record_id: str) -> bool:
        """
        Delete a DNS record.
        
        Args:
            zone_id: Cloudflare zone ID
            record_id: DNS record ID
            
        Returns:
            True if successful
        """
        await self._make_request("DELETE", f"zones/{zone_id}/dns_records/{record_id}")
        logger.info(f"Deleted DNS record {record_id}")
        return True
    
    async def configure_domain_dns(
        self,
        domain: str,
        server_ip: str = None,
        mx_host: str = "heracles.mxrouting.net",
        mx_priority: int = 10
    ) -> Dict:
        """
        Configure complete DNS setup for a domain.
        
        This function:
        1. Creates or gets the Cloudflare zone
        2. Creates A record for root domain
        3. Creates CNAME for www subdomain
        4. Creates MX records for email
        5. Creates SPF record for email authentication
        
        Args:
            domain: Domain name (e.g., "example.com")
            server_ip: Server IP address (defaults to CLOUDFLARE_SERVER_IP from settings)
            mx_host: MX host for email (default: MXRoute)
            mx_priority: MX record priority
            
        Returns:
            Dictionary with zone info and nameservers
        """
        # Use configured server IP or default
        if server_ip is None:
            server_ip = settings.CLOUDFLARE_SERVER_IP
        
        logger.info(f"Configuring DNS for {domain} pointing to {server_ip}")
        
        # Step 1: Get or create zone
        zone = await self.get_or_create_zone(domain)
        zone_id = zone["id"]
        nameservers = zone.get("name_servers", [])
        
        # Step 2: Check if records already exist
        existing_records = await self.list_dns_records(zone_id)
        existing_types = {r["type"]: r for r in existing_records}
        
        # Step 3: Create A record for root domain (@)
        if "A" not in existing_types or existing_types["A"]["name"] != "@":
            await self.create_dns_record(
                zone_id=zone_id,
                record_type="A",
                name="@",
                content=server_ip,
                ttl=3600
            )
        
        # Step 4: Create CNAME for www subdomain
        www_exists = any(r["type"] == "CNAME" and r["name"] == "www" for r in existing_records)
        if not www_exists:
            await self.create_dns_record(
                zone_id=zone_id,
                record_type="CNAME",
                name="www",
                content=domain,
                ttl=3600
            )
        
        # Step 5: Create MX records for email
        mx_records = [r for r in existing_records if r["type"] == "MX"]
        if not mx_records:
            # Primary MX
            await self.create_dns_record(
                zone_id=zone_id,
                record_type="MX",
                name="@",
                content=mx_host,
                priority=mx_priority,
                ttl=3600
            )
            # Secondary MX (relay)
            await self.create_dns_record(
                zone_id=zone_id,
                record_type="MX",
                name="@",
                content="heracles-relay.mxrouting.net",
                priority=mx_priority + 10,
                ttl=3600
            )
        
        # Step 6: Create SPF record
        spf_exists = any(
            r["type"] == "TXT" and "v=spf1" in r.get("content", "") 
            for r in existing_records
        )
        if not spf_exists:
            await self.create_dns_record(
                zone_id=zone_id,
                record_type="TXT",
                name="@",
                content="v=spf1 include:mxroute.com -all",
                ttl=3600
            )
        
        logger.info(f"DNS configuration complete for {domain}")
        
        return {
            "zone_id": zone_id,
            "zone_name": zone.get("name"),
            "nameservers": nameservers,
            "status": zone.get("status")
        }


# Convenience function for easy import
async def configure_client_domain(
    domain: str,
    server_ip: str = None
) -> Dict:
    """
    Configure DNS for a client domain.
    
    This is a convenience wrapper around CloudflareService.configure_domain_dns()
    
    Args:
        domain: Client's domain name
        server_ip: Server IP address (defaults to CLOUDFLARE_SERVER_IP from settings)
        
    Returns:
        Dictionary with zone info and nameservers
    """
    service = CloudflareService()
    # If server_ip not provided, it will use settings.CLOUDFLARE_SERVER_IP in configure_domain_dns
    return await service.configure_domain_dns(domain, server_ip=server_ip)



