export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === '/refresh') {
      const deployHookUrl = "https://api.cloudflare.com/client/v4/pages/hooks/deploy_hooks/YOUR-HOOK-ID";

      const deployResponse = await fetch(deployHookUrl, {
        method: "POST"
      });

      if (deployResponse.status === 204) {
        return new Response('✅ Blog rebuild triggered!', { status: 200 });
      } else {
        return new Response('⚠️ Failed to trigger rebuild.', { status: 500 });
      }
    }

    return new Response('Not Found', { status: 404 });
  }
}
