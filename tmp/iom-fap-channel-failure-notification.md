**Configuration action required — INTERNATIONAL ORGANIZATION FOR MIGRATION**

**Customer details**
- Customer: INTERNATIONAL ORGANIZATION FOR MIGRATION
- Tenant: INTERNATIONAL ORGANIZATION FOR MIGRATION (FAP)
- Org ID: `1106899e-f93e-4de4-b985-8b45f3f1bc9b`
- App Center: PRODEU2
- Partner: Activeo

**Issue summary**
We are seeing **Channel Failure** alerts when queued calls are delivered to agents using **Webex Calling (WxC)**. Engineering analysis shows the **agent telephony leg is rejected with SIP 403 Forbidden** before the agent device rings. Contact Center routing and queueing are operating normally.

- Affected queue: **Islamabad Dari queue**
- Affected site: **Islamabad**
- Alert window: **3 July 2026, ~04:13–04:18 UTC**
- Example interaction: `2ec42df1-ba07-46de-b6a3-e8ab49245ba6`
- Agent routing ID: `072028ca-5e28-4da6-b2a5-8768b816f529`

Typical log pattern:
- `SipFailureReasonAndCode → fsSipCode: 403, fsCause: CALL_REJECTED, participantType: Agent, callLegPlatformType: WxC`
- `AgentInviteFailed → reason CHANNEL_FAILURE, reason code 158`

**Required customer / partner actions**
1. Identify agent `072028ca-5e28-4da6-b2a5-8768b816f529` (Islamabad site) and confirm their WxC extension/DN.
2. Verify **Webex Calling permissions / Class of Service** allow inbound contact-center delivery to that line.
3. Confirm the agent endpoint is correctly provisioned in **WxCC Admin** and **Webex Control Hub**.
4. Test whether the agent can receive a **normal inbound WxC call** on the same line outside Contact Center.
5. Review any **recent changes** to this agent's profile, DN, location, or WxC settings.

**Important**
This is **not** a Cisco platform outage in EU. The failure is consistent with **agent-specific Webex Calling configuration or calling permissions**. If the agent DN, location, or COP settings are incorrect, callers will remain in queue without connecting and Channel Failure alerts may continue.

Please reply in this space once the above is complete.
