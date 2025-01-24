# API Key Management Guide

## Types of API Keys

### Admin Keys
- **Full Access**: Complete control over OpenAI account and resources
- **Permissions**: All actions including billing, key management, and resource access
- **Use Cases**: Account administration, testing, development
- **Security Level**: Highest risk, requires maximum security

### User Keys
- **Limited Access**: Restricted to specific resources and operations
- **Permissions**: Customizable based on application needs
- **Use Cases**: Production applications, team access, external systems
- **Security Level**: Lower risk, suitable for broader distribution

### Normal API Key
**Purpose**:
- General-purpose API authentication
- User-level access to specific resources
- Development and testing environments

**Scope**:
- Limited to specific API endpoints
- Basic operations (e.g., model calls, embeddings)
- User-level permissions

**Usage**:
- Development environments
- Small-scale testing
- Limited functionality scenarios

**Security Level**:
- Medium risk
- Standard security measures
- Regular rotation recommended

### Service Key
**Purpose**:
- Service-to-service communication
- Backend automation
- Production system integration

**Scope**:
- Broader administrative access
- Advanced features and integrations
- System-level operations

**Usage**:
- Production environments
- CI/CD pipelines
- Automated services
- Scheduled tasks

**Security Level**:
- High risk
- Maximum security required
- Strict rotation policy

## Key Comparison Matrix

| Aspect | Normal API Key | Service Key |
|--------|---------------|-------------|
| Purpose | General API access | Automated backend/service access |
| Scope | Limited | Broad or administrative-level |
| Usage | Testing, small-scale apps | Production systems, automation |
| Security Risk | Lower (less access) | Higher (greater access potential) |
| Rotation Period | 90 days | 30 days |
| Storage | Environment variables | Secure key vault |
| Monitoring | Basic logging | Advanced monitoring |

## When to Use Each Key Type

### Admin Keys
✅ **Recommended for**:
- Initial system setup and configuration
- Account management and billing
- Creating and managing other API keys
- Internal testing and development

❌ **Not recommended for**:
- Production applications
- Shared environments
- External services
- Public repositories

### User Keys
✅ **Recommended for**:
- Production deployments
- Team member access
- External integrations
- Specific feature implementations

❌ **Not recommended for**:
- Account management
- Billing operations
- Key management

### Normal API Key
✅ **Recommended for**:
- Development environments
- Small-scale testing
- Limited functionality scenarios

❌ **Not recommended for**:
- Production environments
- CI/CD pipelines
- Automated services
- Scheduled tasks

### Service Key
✅ **Recommended for**:
- Production environments
- CI/CD pipelines
- Automated services
- Scheduled tasks

❌ **Not recommended for**:
- Development environments
- Small-scale testing
- Limited functionality scenarios

## Environment-Specific Usage

### Development Environment
```python
# Use normal API key
api_key = key_manager.get_key("openai_api_dev")
```
- Limited scope
- Local testing
- Quick iteration

### Staging Environment
```python
# Use service key with restricted scope
api_key = key_manager.get_key("openai_service_staging")
```
- Service-level access
- Integration testing
- Pre-production validation

### Production Environment
```python
# Use full service key
api_key = key_manager.get_key("openai_service_prod")
```
- Full service access
- Maximum security
- Continuous monitoring

## Security Best Practices

### 1. Key Storage
- Use environment variables
- Implement secure key vaults
- Never hardcode keys in source code
- Use configuration files outside version control

### 2. Access Control
- Implement principle of least privilege
- Regular access reviews
- Document key assignments
- Maintain key inventory

### 3. Monitoring and Rotation
- Monitor key usage regularly
- Set up usage alerts
- Rotate keys periodically
- Immediate rotation on suspicion of compromise

### 4. Implementation Guidelines
```python
# DON'T - Never hardcode keys
api_key = "sk-1234567890abcdef"

# DO - Use environment variables
import os
api_key = os.getenv("OPENAI_API_KEY")

# DO - Use secure configuration
from key_manager import KeyManager
key_manager = KeyManager()
api_key = key_manager.get_key("openai_user")

# Normal API Key Usage
from key_manager import KeyManager

# Development
key_manager = KeyManager(environment="development")
api_key = key_manager.get_key("openai_api_dev")

# Service Key Usage
# Production Service
key_manager = KeyManager(environment="production")
service_key = key_manager.get_key("openai_service_prod")
```

## Key Management Workflow

1. **Initial Setup**
   - Create admin key securely
   - Store in secure environment
   - Document key creation

2. **User Key Creation**
   - Create with minimal required permissions
   - Assign to specific service/feature
   - Document purpose and owner

3. **Normal API Key Creation**
   - Create with limited scope
   - Assign to development or testing environment
   - Document purpose and owner

4. **Service Key Creation**
   - Create with broader administrative access
   - Assign to production environment or automated service
   - Document purpose and owner

5. **Regular Maintenance**
   - Monitor usage patterns
   - Review access regularly
   - Rotate keys on schedule

6. **Security Incident Response**
   - Immediate key rotation
   - Access pattern analysis
   - Security review
   - Documentation update

## Implementation Example

```python
# Key configuration in config/keys_config.json
{
    "keys": {
        "openai_admin": {
            "type": "admin",
            "description": "OpenAI administrative access",
            "rotation_period_days": 30,
            "last_rotated": "2025-01-19",
            "owner": "System Administrator"
        },
        "openai_user": {
            "type": "user",
            "description": "RAG system API access",
            "rotation_period_days": 90,
            "last_rotated": "2025-01-19",
            "owner": "RAG System"
        },
        "openai_api_dev": {
            "type": "normal",
            "description": "OpenAI API development access",
            "rotation_period_days": 90,
            "last_rotated": "2025-01-19",
            "owner": "Development Team"
        },
        "openai_service_prod": {
            "type": "service",
            "description": "OpenAI service production access",
            "rotation_period_days": 30,
            "last_rotated": "2025-01-19",
            "owner": "Production Team"
        }
    }
}
```

## Security Checklist

- [ ] Keys stored in secure location
- [ ] Environment variables configured
- [ ] Key rotation schedule established
- [ ] Usage monitoring implemented
- [ ] Access documentation maintained
- [ ] Emergency rotation procedure documented
- [ ] Key inventory updated
- [ ] Security incidents logged

### Normal API Keys
- [ ] Stored in environment variables
- [ ] 90-day rotation schedule
- [ ] Basic logging implemented
- [ ] Rate limiting configured
- [ ] Scope restrictions set

### Service Keys
- [ ] Stored in secure vault
- [ ] 30-day rotation schedule
- [ ] Advanced monitoring active
- [ ] IP restrictions configured
- [ ] Audit logging enabled
- [ ] Emergency rotation procedure
- [ ] Access review process
- [ ] Backup procedures
