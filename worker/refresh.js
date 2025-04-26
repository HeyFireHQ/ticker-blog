export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === '/refresh') {            
      const providedKey = url.searchParams.get('key');
      const secretKey = env.REFRESH_SECRET_KEY;
      const deployHookUrl = env.DEPLOY_HOOK_URL;

      if (!providedKey || providedKey !== secretKey) {
        return new Response('Unauthorized', { status: 401 });
      }

      const deployResponse = await fetch(deployHookUrl, {
        method: "POST"
      });

 if (deployResponse.ok) {
        return new Response('✅ Blog rebuild triggered!', { status: 200 });
      } else {
        return new Response('⚠️ Failed to trigger rebuild.', { status: 500 });
      }
    }

    return new Response('Not Found', { status: 404 });
  }
}
