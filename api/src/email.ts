import { SESClient, SendEmailCommand } from '@aws-sdk/client-ses';

const SES_REGION = process.env.SES_REGION || 'ap-southeast-1';
const SES_FROM = process.env.SES_FROM_EMAIL || 'hello@buywhere.ai';
const VERIFY_BASE = process.env.VERIFY_BASE_URL || 'https://api.buywhere.ai';

let sesClient: SESClient | null = null;

function getSesClient(): SESClient | null {
  if (process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY) {
    if (!sesClient) {
      sesClient = new SESClient({
        region: SES_REGION,
        credentials: {
          accessKeyId: process.env.AWS_ACCESS_KEY_ID,
          secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
        },
      });
    }
    return sesClient;
  }
  return null;
}

export async function sendVerificationEmail(
  email: string,
  token: string,
  name?: string
): Promise<boolean> {
  const verifyUrl = `${VERIFY_BASE}/v1/auth/verify?token=${encodeURIComponent(token)}`;
  const greeting = name ? `Hi ${name},` : 'Hi there,';

  const htmlBody = [
    `<!DOCTYPE html>`,
    `<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:560px;margin:0 auto;padding:24px">`,
    `<div style="background:#f8fafc;border-radius:16px;padding:32px">`,
    `<p style="font-size:18px;font-weight:600;color:#0f172a;margin:0 0 16px">Verify your BuyWhere API key</p>`,
    `<p style="font-size:14px;line-height:1.6;color:#334155;margin:0 0 24px">`,
    `${greeting} Thanks for signing up for BuyWhere. Click the button below to verify your email and activate your free tier (60 req/min, 1,000 req/day).`,
    `</p>`,
    `<a href="${verifyUrl}" style="display:inline-block;background:#4f46e5;color:#fff;font-size:14px;font-weight:600;padding:12px 28px;border-radius:12px;text-decoration:none">Verify email address</a>`,
    `<p style="font-size:12px;color:#64748b;margin:24px 0 0;line-height:1.5">`,
    `Or paste this link into your browser:<br/>`,
    `<a href="${verifyUrl}" style="color:#4f46e5">${verifyUrl}</a>`,
    `</p>`,
    `<p style="font-size:12px;color:#94a3b8;margin:24px 0 0;line-height:1.5">`,
    `This link expires in 24 hours. If you didn't sign up for BuyWhere, you can ignore this email.`,
    `</p>`,
    `</div></body></html>`,
  ].join('\n');

  const client = getSesClient();
  if (client) {
    try {
      await client.send(
        new SendEmailCommand({
          Source: SES_FROM,
          Destination: { ToAddresses: [email] },
          Message: {
            Subject: { Data: 'Verify your BuyWhere API key', Charset: 'UTF-8' },
            Body: {
              Html: { Data: htmlBody, Charset: 'UTF-8' },
              Text: {
                Data: `Verify your BuyWhere API key\n\n${greeting}\n\nClick this link to verify your email:\n${verifyUrl}\n\nThis link expires in 24 hours.`,
                Charset: 'UTF-8',
              },
            },
          },
        })
      );
      return true;
    } catch (err) {
      console.error('[email] SES send failed:', err);
      return false;
    }
  }

  console.log(`[email-stub] Would send verification to ${email} with token ${token}`);
  return true;
}
