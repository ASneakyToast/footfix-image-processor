# Anthropic API Setup Guide for FootFix

This guide walks you through setting up an Anthropic API key for FootFix's alt text generation feature.

## Quick Start

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. Open FootFix Preferences (⌘,)
3. Go to Alt Text tab
4. Enter your API key
5. Click "Validate Key"

## Detailed Setup Instructions

### Step 1: Create an Anthropic Account

1. Visit [https://console.anthropic.com](https://console.anthropic.com)
2. Click "Sign Up" or "Log In"
3. Complete registration with your email
4. Verify your email address

### Step 2: Access API Keys

1. Log in to the Anthropic Console
2. Navigate to "API Keys" in the sidebar
3. You'll see the API Keys management page

### Step 3: Create a New API Key

1. Click "Create Key" button
2. Give your key a descriptive name (e.g., "FootFix Alt Text")
3. Select appropriate permissions (default is fine)
4. Click "Create"
5. **Important**: Copy the key immediately - it won't be shown again!

The key will look like: `sk-ant-api03-xxxxxxxxxxxxx`

### Step 4: Configure FootFix

1. Open FootFix application
2. Go to Preferences (⌘, on Mac)
3. Click on the "Alt Text" tab
4. You'll see the API configuration section

### Step 5: Enter Your API Key

1. Paste your API key in the secure field
2. The key is stored securely in your system keychain
3. Click "Validate Key" to test the connection
4. You should see "API key is valid" message

### Step 6: Configure Settings (Optional)

- **Enable Cost Tracking**: Track API usage and costs
- **Show Cost Estimates**: Display cost before processing
- **Monthly Budget Alert**: Get notified when approaching limit

## API Key Security

### Best Practices

1. **Never share your API key**
   - Treat it like a password
   - Don't commit to version control
   - Don't post in forums or support tickets

2. **Use dedicated keys**
   - Create separate keys for different applications
   - Name keys descriptively
   - Rotate keys periodically

3. **Monitor usage**
   - Check Anthropic Console regularly
   - Set up usage alerts
   - Review monthly statements

### Key Storage

FootFix stores your API key securely:
- Encrypted in system keychain (macOS)
- Never stored in plain text
- Not included in preferences export
- Isolated from other applications

## Billing and Costs

### Understanding Pricing

- Claude 3 Sonnet: ~$3 per million input tokens
- Average image analysis: ~2,000 tokens
- Estimated cost: ~$0.006 per image

### Setting Up Billing

1. Go to Anthropic Console
2. Navigate to "Billing"
3. Add payment method
4. Set monthly spending limits (optional)

### Cost Examples

| Usage | Monthly Cost |
|-------|--------------|
| 100 images | ~$0.60 |
| 500 images | ~$3.00 |
| 1,000 images | ~$6.00 |
| 5,000 images | ~$30.00 |

## Troubleshooting

### "Invalid API Key" Error

**Symptoms**: Error when validating or using key

**Solutions**:
1. Check for extra spaces or characters
2. Ensure key starts with `sk-ant-api`
3. Verify key hasn't been revoked
4. Create a new key if needed

### "Rate Limited" Error

**Symptoms**: Requests failing with rate limit message

**Solutions**:
1. FootFix handles rate limits automatically
2. Upgrade your Anthropic plan if needed
3. Process smaller batches
4. Wait and retry

### "Billing Issue" Error

**Symptoms**: API calls fail despite valid key

**Solutions**:
1. Check billing status in Anthropic Console
2. Verify payment method is valid
3. Check if monthly limit reached
4. Add credits to account

### Connection Issues

**Symptoms**: Network errors or timeouts

**Solutions**:
1. Check internet connection
2. Verify firewall settings
3. Disable VPN temporarily
4. Try different network

## API Limits and Quotas

### Default Limits

- **Rate Limit**: 50 requests/minute
- **Monthly Token Limit**: Based on plan
- **Max Tokens per Request**: 300 (for alt text)

### Upgrading Limits

1. Contact Anthropic support
2. Explain your use case
3. Request higher limits
4. Provide usage estimates

## Managing Multiple Keys

### When to Use Multiple Keys

- Different projects or clients
- Development vs. production
- Team member access control
- Budget separation

### Switching Keys in FootFix

1. Open Preferences
2. Go to Alt Text tab
3. Clear current key
4. Enter new key
5. Validate new key

## API Key Rotation

### Why Rotate Keys

- Security best practice
- Compliance requirements
- Suspected compromise
- Regular maintenance

### How to Rotate

1. Create new key in Anthropic Console
2. Update FootFix with new key
3. Verify new key works
4. Delete old key from Console

## Monitoring Usage

### In FootFix

- View usage statistics in Preferences
- See per-session costs
- Track monthly totals
- Monitor trends

### In Anthropic Console

- Detailed usage graphs
- Token consumption
- Cost breakdown
- API call logs

## Team Setup

### Sharing Access

1. **Option 1**: Shared Anthropic Account
   - Single billing source
   - Centralized management
   - Shared usage limits

2. **Option 2**: Individual Keys
   - Per-user billing
   - Independent limits
   - Better security

### Best Practices for Teams

1. Use descriptive key names
2. Document key ownership
3. Regular access reviews
4. Establish usage guidelines

## Advanced Configuration

### Environment Variables

For automated workflows:
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-xxxxx"
```

### Proxy Configuration

If behind corporate proxy:
1. Configure system proxy settings
2. FootFix will use system configuration
3. May need IT approval for API access

### API Endpoints

FootFix uses:
- Endpoint: `https://api.anthropic.com/v1/messages`
- Model: Claude 3 Sonnet
- Region: Automatic

## Getting Help

### Resources

1. **Anthropic Documentation**: [docs.anthropic.com](https://docs.anthropic.com)
2. **Support Contact**: support@anthropic.com
3. **Status Page**: [status.anthropic.com](https://status.anthropic.com)
4. **FootFix Support**: Via application Help menu

### Common Questions

**Q: Can I use the same key for other applications?**
A: Yes, but we recommend separate keys for better tracking.

**Q: What happens if I exceed my limit?**
A: Requests will fail until the next billing period or limit increase.

**Q: Is the API key tied to my computer?**
A: No, you can use the same key on multiple machines.

**Q: How do I cancel my API access?**
A: Delete all API keys in Anthropic Console and remove billing method.

## Conclusion

With your Anthropic API key configured, you're ready to use FootFix's powerful alt text generation features. Remember to monitor your usage and follow security best practices to ensure smooth operation.