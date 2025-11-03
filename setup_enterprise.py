"""
🚀 ENTERPRISE MIGRATION & SETUP SCRIPT
Migrate from single-tenant to multi-tenant architecture
"""

from models.database import db as old_db
from models.database_enterprise import enterprise_db
from werkzeug.security import generate_password_hash
import os
from datetime import datetime

def create_super_admin():
    """Create the first super admin account"""
    print("\n🔐 Creating Super Admin Account...")
    
    super_admin_data = {
        "email": os.getenv("SUPER_ADMIN_EMAIL", "superadmin@claimlens.com"),
        "password": generate_password_hash(os.getenv("SUPER_ADMIN_PASSWORD", "SuperAdmin@2025")),
        "name": "ClaimLens Super Admin",
        "user_type": "super_admin",
        "status": "active",
        "created_by": "system"
    }
    
    # Check if super admin already exists
    existing = enterprise_db.get_user_by_email(super_admin_data['email'])
    if existing:
        print(f"✅ Super admin already exists: {super_admin_data['email']}")
        return existing['_id']
    
    user_id = enterprise_db.create_user(super_admin_data)
    print(f"✅ Super admin created: {super_admin_data['email']}")
    print(f"   Password: {os.getenv('SUPER_ADMIN_PASSWORD', 'SuperAdmin@2025')}")
    return user_id


def create_demo_companies():
    """Create demo insurance companies"""
    print("\n🏢 Creating Demo Insurance Companies...")
    
    companies = [
        {
            "name": "ICICI Lombard",
            "insurance_types": ["Health", "Vehicle", "Travel"],
            "contact": "+91-1860-266-7766",
            "logo": "https://www.icicilombard.com/logo.png",
            "created_by": "superadmin@claimlens.com"
        },
        {
            "name": "HDFC ERGO",
            "insurance_types": ["Health", "Vehicle", "Home"],
            "contact": "+91-1800-266-8000",
            "logo": "https://www.hdfcergo.com/logo.png",
            "created_by": "superadmin@claimlens.com"
        },
        {
            "name": "LIC India",
            "insurance_types": ["Health", "Life", "Pension"],
            "contact": "+91-022-6827-6827",
            "logo": "https://www.licindia.in/logo.png",
            "created_by": "superadmin@claimlens.com"
        }
    ]
    
    company_ids = []
    for company in companies:
        existing = enterprise_db.get_company_by_name(company['name'])
        if existing:
            print(f"✅ Company already exists: {company['name']}")
            company_ids.append(existing['_id'])
        else:
            company_id = enterprise_db.create_company(company)
            print(f"✅ Created company: {company['name']}")
            company_ids.append(company_id)
    
    return company_ids


def create_demo_company_admins(company_ids):
    """Create demo company admin accounts"""
    print("\n👔 Creating Demo Company Admins...")
    
    admins = [
        {
            "email": "admin@icicilombard.com",
            "password": "ICICI@Admin123",
            "name": "ICICI Admin",
            "company_id": company_ids[0]
        },
        {
            "email": "admin@hdfcergo.com",
            "password": "HDFC@Admin123",
            "name": "HDFC Admin",
            "company_id": company_ids[1]
        },
        {
            "email": "admin@lic.in",
            "password": "LIC@Admin123",
            "name": "LIC Admin",
            "company_id": company_ids[2]
        }
    ]
    
    admin_ids = []
    for admin in admins:
        existing = enterprise_db.get_user_by_email(admin['email'])
        if existing:
            print(f"✅ Company admin already exists: {admin['email']}")
            admin_ids.append(existing['_id'])
        else:
            admin_data = {
                "email": admin['email'],
                "password": generate_password_hash(admin['password']),
                "name": admin['name'],
                "user_type": "company_admin",
                "company_id": admin['company_id'],
                "status": "active",
                "created_by": "superadmin@claimlens.com"
            }
            admin_id = enterprise_db.create_user(admin_data)
            print(f"✅ Created company admin: {admin['email']} | Password: {admin['password']}")
            admin_ids.append(admin_id)
    
    return admin_ids


def create_demo_agents(company_ids):
    """Create demo insurance agents"""
    print("\n👮 Creating Demo Insurance Agents...")
    
    agents = [
        {
            "email": "agent1@icicilombard.com",
            "password": "Agent@123",
            "name": "Rajesh Kumar",
            "company_id": company_ids[0],
            "employee_id": "ICICI-001"
        },
        {
            "email": "agent2@icicilombard.com",
            "password": "Agent@123",
            "name": "Priya Sharma",
            "company_id": company_ids[0],
            "employee_id": "ICICI-002"
        },
        {
            "email": "agent1@hdfcergo.com",
            "password": "Agent@123",
            "name": "Amit Patel",
            "company_id": company_ids[1],
            "employee_id": "HDFC-001"
        },
        {
            "email": "agent1@lic.in",
            "password": "Agent@123",
            "name": "Sunita Rao",
            "company_id": company_ids[2],
            "employee_id": "LIC-001"
        }
    ]
    
    agent_ids = []
    for agent in agents:
        existing = enterprise_db.get_user_by_email(agent['email'])
        if existing:
            print(f"✅ Agent already exists: {agent['email']}")
            agent_ids.append(existing['_id'])
        else:
            agent_data = {
                "email": agent['email'],
                "password": generate_password_hash(agent['password']),
                "name": agent['name'],
                "user_type": "agent",
                "company_id": agent['company_id'],
                "employee_id": agent['employee_id'],
                "status": "active",  # Pre-approved for demo
                "created_by": "system"
            }
            agent_id = enterprise_db.create_user(agent_data)
            print(f"✅ Created agent: {agent['email']} | Password: {agent['password']}")
            agent_ids.append(agent_id)
    
    return agent_ids


def create_demo_customers(company_ids):
    """Create demo customer accounts"""
    print("\n👤 Creating Demo Customers...")
    
    customers = [
        {
            "email": "customer1@gmail.com",
            "password": "Customer@123",
            "name": "Arjun Mehta",
            "company_id": company_ids[0]  # ICICI
        },
        {
            "email": "customer2@gmail.com",
            "password": "Customer@123",
            "name": "Sneha Iyer",
            "company_id": company_ids[1]  # HDFC
        }
    ]
    
    customer_ids = []
    for customer in customers:
        existing = enterprise_db.get_user_by_email(customer['email'])
        if existing:
            print(f"✅ Customer already exists: {customer['email']}")
            customer_ids.append(existing['_id'])
        else:
            customer_data = {
                "email": customer['email'],
                "password": generate_password_hash(customer['password']),
                "name": customer['name'],
                "user_type": "customer",
                "company_id": customer['company_id'],
                "status": "active",
                "created_by": "system"
            }
            customer_id = enterprise_db.create_user(customer_data)
            print(f"✅ Created customer: {customer['email']} | Password: {customer['password']}")
            customer_ids.append(customer_id)
    
    return customer_ids


def display_credentials():
    """Display all demo credentials"""
    print("\n" + "="*80)
    print("🎉 ENTERPRISE SETUP COMPLETE!")
    print("="*80)
    
    print("\n📋 DEMO CREDENTIALS:\n")
    
    print("🔐 SUPER ADMIN:")
    print(f"   Email: superadmin@claimlens.com")
    print(f"   Password: SuperAdmin@2025")
    print(f"   Access: /api/super-admin/*")
    
    print("\n👔 COMPANY ADMINS:")
    admins = [
        ("admin@icicilombard.com", "ICICI@Admin123", "ICICI Lombard"),
        ("admin@hdfcergo.com", "HDFC@Admin123", "HDFC ERGO"),
        ("admin@lic.in", "LIC@Admin123", "LIC India")
    ]
    for email, password, company in admins:
        print(f"   {company}:")
        print(f"      Email: {email}")
        print(f"      Password: {password}")
        print(f"      Access: /api/company-admin/*")
    
    print("\n👮 INSURANCE AGENTS:")
    agents = [
        ("agent1@icicilombard.com", "Agent@123", "Rajesh Kumar", "ICICI"),
        ("agent2@icicilombard.com", "Agent@123", "Priya Sharma", "ICICI"),
        ("agent1@hdfcergo.com", "Agent@123", "Amit Patel", "HDFC"),
        ("agent1@lic.in", "Agent@123", "Sunita Rao", "LIC")
    ]
    for email, password, name, company in agents:
        print(f"   {name} ({company}):")
        print(f"      Email: {email}")
        print(f"      Password: {password}")
        print(f"      Access: /api/agent/*")
    
    print("\n👤 CUSTOMERS:")
    customers = [
        ("customer1@gmail.com", "Customer@123", "Arjun Mehta", "ICICI"),
        ("customer2@gmail.com", "Customer@123", "Sneha Iyer", "HDFC")
    ]
    for email, password, name, company in customers:
        print(f"   {name} ({company}):")
        print(f"      Email: {email}")
        print(f"      Password: {password}")
        print(f"      Access: /api/claims/*")
    
    print("\n" + "="*80)
    print("🚀 START THE SERVER: python app.py")
    print("📚 API DOCUMENTATION: See API_DOCS_ENTERPRISE.md")
    print("🏆 HACKATHON DEMO: See HACKATHON_READY.md")
    print("="*80 + "\n")


def main():
    """Main migration function"""
    print("\n" + "="*80)
    print("🚀 CLAIMLENS ENTERPRISE SETUP")
    print("="*80)
    
    try:
        # Step 1: Create super admin
        super_admin_id = create_super_admin()
        
        # Step 2: Create demo companies
        company_ids = create_demo_companies()
        
        # Step 3: Create company admins
        admin_ids = create_demo_company_admins(company_ids)
        
        # Step 4: Create agents
        agent_ids = create_demo_agents(company_ids)
        
        # Step 5: Create customers
        customer_ids = create_demo_customers(company_ids)
        
        # Display all credentials
        display_credentials()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
