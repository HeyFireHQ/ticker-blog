import bcrypt from 'bcryptjs';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const { pathname, searchParams } = url;

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Route handling
      if (pathname === '/auth/login') {
        return await handleLogin(request, env, corsHeaders);
      } else if (pathname === '/auth/verify') {
        return await handleVerifyToken(request, env, corsHeaders);
      } else if (pathname.startsWith('/posts')) {
        return await handlePosts(request, env, corsHeaders, pathname);
      } else if (pathname.startsWith('/images')) {
        return await handleImages(request, env, corsHeaders, pathname);
      } else if (pathname === '/deploy') {
        return await handleDeploy(request, env, corsHeaders);
      } else if (pathname.startsWith('/users')) {
        return await handleUsers(request, env, corsHeaders, pathname);
      } else if (pathname === '/refresh') {
        return await handleRefresh(request, env, corsHeaders);
      }

      return new Response('Not Found', { status: 404, headers: corsHeaders });
    } catch (error) {
      console.error('API Error:', error);
      return new Response('Internal Server Error: ' + error.message, { 
        status: 500, 
        headers: corsHeaders 
      });
    }
  }
};

// Authentication functions
async function handleLogin(request, env, corsHeaders) {
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { status: 405, headers: corsHeaders });
  }

  const { email, password } = await request.json();

  // Get user from D1
  const user = await env.DB.prepare('SELECT * FROM users WHERE email = ? AND is_admin = 1')
    .bind(email)
    .first();

  if (!user) {
    return new Response(JSON.stringify({ error: 'Invalid credentials' }), {
      status: 401,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  // Verify password
  const isValid = await bcrypt.compare(password, user.password_hash);
  if (!isValid) {
    return new Response(JSON.stringify({ error: 'Invalid credentials' }), {
      status: 401,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  // Create JWT token (simplified - in production use proper JWT library)
  const token = btoa(JSON.stringify({
    userId: user.id,
    email: user.email,
    isAdmin: user.is_admin,
    exp: Date.now() + (24 * 60 * 60 * 1000) // 24 hours
  }));

  return new Response(JSON.stringify({
    token,
    user: {
      id: user.id,
      email: user.email,
      isAdmin: user.is_admin
    }
  }), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

async function handleVerifyToken(request, env, corsHeaders) {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return new Response(JSON.stringify({ error: 'No token provided' }), {
      status: 401,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  try {
    const token = authHeader.substring(7);
    const payload = JSON.parse(atob(token));

    if (payload.exp < Date.now()) {
      return new Response(JSON.stringify({ error: 'Token expired' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    return new Response(JSON.stringify({
      user: {
        id: payload.userId,
        email: payload.email,
        isAdmin: payload.isAdmin
      }
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Invalid token' }), {
      status: 401,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

// Posts management functions - Now loads from GitHub
async function handlePosts(request, env, corsHeaders, pathname) {
  const user = await authenticateRequest(request);
  if (!user || !user.isAdmin) {
    return new Response(JSON.stringify({ error: 'Admin access required' }), {
      status: 403,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  const segments = pathname.split('/');
  const postId = segments[2];

  switch (request.method) {
    case 'GET':
      if (postId) {
        return await getPostFromGitHub(env, corsHeaders, postId);
      } else {
        return await getPostsFromGitHub(env, corsHeaders);
      }

    case 'POST':
      return await createPost(request, env, corsHeaders, user.userId);

    case 'PUT':
      if (!postId) {
        return new Response(JSON.stringify({ error: 'Post ID required' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      return await updatePost(request, env, corsHeaders, postId, user.userId);

    case 'DELETE':
      if (!postId) {
        return new Response(JSON.stringify({ error: 'Post ID required' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      return await deletePost(env, corsHeaders, postId, user.userId);

    default:
      return new Response('Method not allowed', { status: 405, headers: corsHeaders });
  }
}

// GitHub Integration Functions
async function getPostsFromGitHub(env, corsHeaders) {
  try {
    const githubToken = env.GITHUB_TOKEN;
    const githubRepo = env.GITHUB_REPO; // format: "owner/repo"
    const githubBranch = env.GITHUB_DEPLOY_BRANCH || 'gh-pages';

    if (!githubToken || !githubRepo) {
      // Fallback to database if GitHub not configured
      return await getPostsFromDatabase(env, corsHeaders);
    }

    // Get content directory from GitHub
    const apiUrl = `https://api.github.com/repos/${githubRepo}/contents/content?ref=${githubBranch}`;
    
    const response = await fetch(apiUrl, {
      headers: {
        'Authorization': `token ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'CardPress-Worker'
      }
    });

    if (!response.ok) {
      console.log('GitHub API error:', await response.text());
      // Fallback to database
      return await getPostsFromDatabase(env, corsHeaders);
    }

    const files = await response.json();
    const posts = [];

    // Process markdown files
    for (const file of files) {
      if (file.name.endsWith('.md') && file.type === 'file') {
        try {
          const post = await parsePostFromGitHub(env, file, githubRepo, githubBranch);
          if (post) {
            posts.push(post);
          }
        } catch (error) {
          console.error('Error parsing post:', file.name, error);
        }
      }
    }

    // Sort by date (newest first)
    posts.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

    return new Response(JSON.stringify(posts), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('GitHub integration error:', error);
    // Fallback to database
    return await getPostsFromDatabase(env, corsHeaders);
  }
}

async function parsePostFromGitHub(env, file, githubRepo, githubBranch) {
  const githubToken = env.GITHUB_TOKEN;
  
  // Get file content
  const contentResponse = await fetch(file.download_url, {
    headers: {
      'Authorization': `token ${githubToken}`,
      'User-Agent': 'CardPress-Worker'
    }
  });

  if (!contentResponse.ok) {
    return null;
  }

  const content = await contentResponse.text();
  
  // Parse frontmatter and content
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!frontmatterMatch) {
    return null;
  }

  const frontmatter = frontmatterMatch[1];
  const postContent = frontmatterMatch[2].trim();

  // Parse frontmatter fields
  const metadata = {};
  frontmatter.split('\n').forEach(line => {
    const match = line.match(/^([^:]+):\s*(.*)$/);
    if (match) {
      const key = match[1].trim();
      let value = match[2].trim();
      
      // Remove quotes if present
      if ((value.startsWith('"') && value.endsWith('"')) || 
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      
      metadata[key] = value;
    }
  });

  // Determine status based on GitHub branch and metadata
  let column_status = 'deployed'; // Default for posts on deploy branch
  if (metadata.status) {
    column_status = metadata.status;
  }

  // Create post object compatible with admin interface
  return {
    id: metadata.slug || file.name.replace('.md', ''),
    title: metadata.title || 'Untitled',
    content: postContent,
    labels: JSON.stringify(metadata.tags ? metadata.tags.split(', ') : []),
    colors: metadata.colors || '',
    column_status: column_status,
    image_url: metadata.image || '',
    image_path: '',
    created_at: metadata.date || file.last_modified || new Date().toISOString(),
    updated_at: file.last_modified || new Date().toISOString(),
    user_id: 'github-sync',
    github_file: file.name,
    github_sha: file.sha
  };
}

async function getPostFromGitHub(env, corsHeaders, postId) {
  try {
    const githubToken = env.GITHUB_TOKEN;
    const githubRepo = env.GITHUB_REPO;
    const githubBranch = env.GITHUB_DEPLOY_BRANCH || 'gh-pages';

    if (!githubToken || !githubRepo) {
      return await getPostFromDatabase(env, corsHeaders, postId);
    }

    // Try to find the post file
    const fileName = `${postId}.md`;
    const apiUrl = `https://api.github.com/repos/${githubRepo}/contents/content/${fileName}?ref=${githubBranch}`;
    
    const response = await fetch(apiUrl, {
      headers: {
        'Authorization': `token ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'CardPress-Worker'
      }
    });

    if (!response.ok) {
      return await getPostFromDatabase(env, corsHeaders, postId);
    }

    const file = await response.json();
    const post = await parsePostFromGitHub(env, file, githubRepo, githubBranch);

    if (!post) {
      return new Response(JSON.stringify({ error: 'Post not found' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    return new Response(JSON.stringify(post), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Error getting post from GitHub:', error);
    return await getPostFromDatabase(env, corsHeaders, postId);
  }
}

// Fallback database functions
async function getPostsFromDatabase(env, corsHeaders) {
  const posts = await env.DB.prepare(
    'SELECT * FROM posts ORDER BY updated_at DESC'
  ).all();

  return new Response(JSON.stringify(posts.results), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

async function getPostFromDatabase(env, corsHeaders, postId) {
  const post = await env.DB.prepare('SELECT * FROM posts WHERE id = ?')
    .bind(postId)
    .first();

  if (!post) {
    return new Response(JSON.stringify({ error: 'Post not found' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  return new Response(JSON.stringify(post), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

// Keep database posts management for creating/editing (before deployment)
async function createPost(request, env, corsHeaders, userId) {
  const postData = await request.json();
  const postId = generateId();

  const result = await env.DB.prepare(`
    INSERT INTO posts (id, user_id, title, content, labels, colors, column_status, image_url, image_path, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
  `).bind(
    postId,
    userId,
    postData.title,
    postData.content,
    JSON.stringify(postData.labels || []),
    postData.colors || '',
    postData.column || 'ideas',
    postData.imageUrl || '',
    postData.imagePath || ''
  ).run();

  if (result.success) {
    const post = await env.DB.prepare('SELECT * FROM posts WHERE id = ?')
      .bind(postId)
      .first();

    return new Response(JSON.stringify(post), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  } else {
    return new Response(JSON.stringify({ error: 'Failed to create post' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

async function updatePost(request, env, corsHeaders, postId, userId) {
  const postData = await request.json();

  const result = await env.DB.prepare(`
    UPDATE posts 
    SET title = ?, content = ?, labels = ?, colors = ?, column_status = ?, 
        image_url = ?, image_path = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
  `).bind(
    postData.title,
    postData.content,
    JSON.stringify(postData.labels || []),
    postData.colors || '',
    postData.column || 'ideas',
    postData.imageUrl || '',
    postData.imagePath || '',
    postId
  ).run();

  if (result.success && result.changes > 0) {
    const post = await env.DB.prepare('SELECT * FROM posts WHERE id = ?')
      .bind(postId)
      .first();

    return new Response(JSON.stringify(post), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  } else {
    return new Response(JSON.stringify({ error: 'Post not found or unauthorized' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

async function deletePost(env, corsHeaders, postId, userId) {
  // Delete from database (draft)
  const result = await env.DB.prepare('DELETE FROM posts WHERE id = ?')
    .bind(postId)
    .run();

  if (result.success && result.changes > 0) {
    return new Response(JSON.stringify({ success: true, message: 'Post deleted' }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  } else {
    return new Response(JSON.stringify({ error: 'Failed to delete post' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

// User management functions (unchanged)
async function handleUsers(request, env, corsHeaders, pathname) {
  const user = await authenticateRequest(request);
  if (!user || !user.isAdmin) {
    return new Response(JSON.stringify({ error: 'Admin access required' }), {
      status: 403,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  const segments = pathname.split('/');
  const userId = segments[2];

  switch (request.method) {
    case 'GET':
      if (userId) {
        return await getUser(env, corsHeaders, userId);
      } else {
        return await getUsers(env, corsHeaders);
      }

    case 'POST':
      return await createUser(request, env, corsHeaders);

    case 'PUT':
      if (!userId) {
        return new Response(JSON.stringify({ error: 'User ID required' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      return await updateUser(request, env, corsHeaders, userId);

    case 'DELETE':
      if (!userId) {
        return new Response(JSON.stringify({ error: 'User ID required' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      return await deleteUser(env, corsHeaders, userId);

    default:
      return new Response('Method not allowed', { status: 405, headers: corsHeaders });
  }
}

async function getUsers(env, corsHeaders) {
  const users = await env.DB.prepare(
    'SELECT id, email, is_admin, created_at, updated_at FROM users WHERE is_admin = 1 ORDER BY created_at DESC'
  ).all();

  return new Response(JSON.stringify(users.results), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

async function getUser(env, corsHeaders, userId) {
  const user = await env.DB.prepare(
    'SELECT id, email, is_admin, created_at, updated_at FROM users WHERE id = ? AND is_admin = 1'
  ).bind(userId).first();

  if (!user) {
    return new Response(JSON.stringify({ error: 'User not found' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  return new Response(JSON.stringify(user), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

async function createUser(request, env, corsHeaders) {
  const userData = await request.json();
  const userId = generateId();

  // Hash password
  const passwordHash = await bcrypt.hash(userData.password, 12);

  const result = await env.DB.prepare(`
    INSERT INTO users (id, email, password_hash, is_admin, created_at, updated_at)
    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
  `).bind(
    userId,
    userData.email,
    passwordHash
  ).run();

  if (result.success) {
    const user = await env.DB.prepare(
      'SELECT id, email, is_admin, created_at, updated_at FROM users WHERE id = ?'
    ).bind(userId).first();

    return new Response(JSON.stringify(user), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  } else {
    return new Response(JSON.stringify({ error: 'Failed to create user' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

async function updateUser(request, env, corsHeaders, userId) {
  const userData = await request.json();

  let query = 'UPDATE users SET email = ?, updated_at = CURRENT_TIMESTAMP';
  let params = [userData.email];

  // Only update password if provided
  if (userData.password) {
    const passwordHash = await bcrypt.hash(userData.password, 12);
    query += ', password_hash = ?';
    params.push(passwordHash);
  }

  query += ' WHERE id = ? AND is_admin = 1';
  params.push(userId);

  const result = await env.DB.prepare(query).bind(...params).run();

  if (result.success && result.changes > 0) {
    const user = await env.DB.prepare(
      'SELECT id, email, is_admin, created_at, updated_at FROM users WHERE id = ?'
    ).bind(userId).first();

    return new Response(JSON.stringify(user), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  } else {
    return new Response(JSON.stringify({ error: 'User not found or unauthorized' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

async function deleteUser(env, corsHeaders, userId) {
  // Don't allow deleting the last admin
  const adminCount = await env.DB.prepare(
    'SELECT COUNT(*) as count FROM users WHERE is_admin = 1'
  ).first();

  if (adminCount.count <= 1) {
    return new Response(JSON.stringify({ error: 'Cannot delete the last admin user' }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  const result = await env.DB.prepare('DELETE FROM users WHERE id = ? AND is_admin = 1')
    .bind(userId)
    .run();

  if (result.success && result.changes > 0) {
    return new Response(JSON.stringify({ success: true, message: 'User deleted' }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  } else {
    return new Response(JSON.stringify({ error: 'User not found or unauthorized' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

// Deploy function - Now pushes to GitHub
async function handleDeploy(request, env, corsHeaders) {
  const user = await authenticateRequest(request);
  if (!user || !user.isAdmin) {
    return new Response(JSON.stringify({ error: 'Admin access required' }), {
      status: 403,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  if (request.method !== 'POST') {
    return new Response('Method not allowed', { status: 405, headers: corsHeaders });
  }

  try {
    // Get deployed posts from database
    const deployedPosts = await env.DB.prepare(
      'SELECT * FROM posts WHERE column_status = ? ORDER BY updated_at DESC'
    ).bind('deployed').all();

    if (deployedPosts.results.length === 0) {
      return new Response(JSON.stringify({ 
        error: 'No posts in deployed status',
        message: 'Move posts to "Deployed" column first'
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Generate and push to GitHub
    const result = await generateAndPushToGitHub(env, deployedPosts.results);
    
    if (result.success) {
      return new Response(JSON.stringify({
        success: true,
        message: `Generated and pushed ${deployedPosts.results.length} posts to GitHub`,
        deployedCount: deployedPosts.results.length,
        githubCommit: result.commitSha,
        pagesUrl: result.pagesUrl
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    } else {
      return new Response(JSON.stringify({
        error: 'Deployment failed',
        message: result.error
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

  } catch (error) {
    console.error('Deploy error:', error);
    return new Response(JSON.stringify({ 
      error: 'Deployment failed',
      message: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

async function generateAndPushToGitHub(env, posts) {
  const githubToken = env.GITHUB_TOKEN;
  const githubRepo = env.GITHUB_REPO; // "owner/repo"
  const githubBranch = env.GITHUB_DEPLOY_BRANCH || 'gh-pages';
  
  if (!githubToken || !githubRepo) {
    return { success: false, error: 'GitHub configuration missing' };
  }

  try {
    // Get current branch SHA
    const branchResponse = await fetch(
      `https://api.github.com/repos/${githubRepo}/git/refs/heads/${githubBranch}`,
      {
        headers: {
          'Authorization': `token ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'CardPress-Worker'
        }
      }
    );

    let baseSha;
    if (branchResponse.ok) {
      const branchData = await branchResponse.json();
      baseSha = branchData.object.sha;
    } else {
      // Branch doesn't exist, get main/master branch SHA
      const mainResponse = await fetch(
        `https://api.github.com/repos/${githubRepo}/git/refs/heads/main`,
        {
          headers: {
            'Authorization': `token ${githubToken}`,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'CardPress-Worker'
          }
        }
      );
      
      if (mainResponse.ok) {
        const mainData = await mainResponse.json();
        baseSha = mainData.object.sha;
      } else {
        return { success: false, error: 'Could not find base branch' };
      }
    }

    // Create tree with all markdown files
    const treeItems = [];
    
    // Add content directory
    for (const post of posts) {
      const labels = JSON.parse(post.labels || '[]');
      const content = createMarkdownContent(post, labels);
      const fileName = `content/${post.id}.md`;
      
      // Create blob for the file
      const blobResponse = await fetch(
        `https://api.github.com/repos/${githubRepo}/git/blobs`,
        {
          method: 'POST',
          headers: {
            'Authorization': `token ${githubToken}`,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'CardPress-Worker',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: btoa(unescape(encodeURIComponent(content))), // Base64 encode
            encoding: 'base64'
          })
        }
      );

      if (!blobResponse.ok) {
        console.error('Failed to create blob for', fileName);
        continue;
      }

      const blobData = await blobResponse.json();
      treeItems.push({
        path: fileName,
        mode: '100644',
        type: 'blob',
        sha: blobData.sha
      });
    }

    // Add Pelican configuration files
    const pelicanConf = createPelicanConfig();
    const publishConf = createPublishConfig();
    
    // Create blobs for config files
    const pelicanBlob = await createGitHubBlob(env, pelicanConf, githubRepo, githubToken);
    const publishBlob = await createGitHubBlob(env, publishConf, githubRepo, githubToken);
    
    if (pelicanBlob && publishBlob) {
      treeItems.push(
        {
          path: 'pelicanconf.py',
          mode: '100644',
          type: 'blob',
          sha: pelicanBlob.sha
        },
        {
          path: 'publishconf.py',
          mode: '100644',
          type: 'blob',
          sha: publishBlob.sha
        }
      );
    }

    // Create tree
    const treeResponse = await fetch(
      `https://api.github.com/repos/${githubRepo}/git/trees`,
      {
        method: 'POST',
        headers: {
          'Authorization': `token ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'CardPress-Worker',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tree: treeItems
        })
      }
    );

    if (!treeResponse.ok) {
      return { success: false, error: 'Failed to create Git tree' };
    }

    const treeData = await treeResponse.json();

    // Create commit
    const commitResponse = await fetch(
      `https://api.github.com/repos/${githubRepo}/git/commits`,
      {
        method: 'POST',
        headers: {
          'Authorization': `token ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'CardPress-Worker',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: `Deploy ${posts.length} posts via CardPress UI`,
          tree: treeData.sha,
          parents: [baseSha]
        })
      }
    );

    if (!commitResponse.ok) {
      return { success: false, error: 'Failed to create commit' };
    }

    const commitData = await commitResponse.json();

    // Update branch reference
    const updateRefResponse = await fetch(
      `https://api.github.com/repos/${githubRepo}/git/refs/heads/${githubBranch}`,
      {
        method: branchResponse.ok ? 'PATCH' : 'POST',
        headers: {
          'Authorization': `token ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'CardPress-Worker',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          sha: commitData.sha,
          ...(branchResponse.ok ? {} : { ref: `refs/heads/${githubBranch}` })
        })
      }
    );

    if (!updateRefResponse.ok) {
      return { success: false, error: 'Failed to update branch' };
    }

    return {
      success: true,
      commitSha: commitData.sha,
      pagesUrl: `https://github.com/${githubRepo}/tree/${githubBranch}`
    };

  } catch (error) {
    console.error('GitHub deployment error:', error);
    return { success: false, error: error.message };
  }
}

async function createGitHubBlob(env, content, githubRepo, githubToken) {
  try {
    const response = await fetch(
      `https://api.github.com/repos/${githubRepo}/git/blobs`,
      {
        method: 'POST',
        headers: {
          'Authorization': `token ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'CardPress-Worker',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          content: btoa(unescape(encodeURIComponent(content))),
          encoding: 'base64'
        })
      }
    );

    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error('Error creating GitHub blob:', error);
  }
  return null;
}

function createMarkdownContent(post, labels) {
  const date = new Date(post.created_at);
  return `---
title: ${post.title}
date: ${date.toISOString().split('T')[0]}
slug: ${post.id}
tags: ${labels.join(', ')}
status: ${post.column_status}
${post.image_url ? `image: ${post.image_url}` : ''}
${post.colors ? `colors: ${post.colors}` : ''}
---

${post.content}
`;
}

function createPelicanConfig() {
  return `#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'CardPress Admin'
SITENAME = 'CardPress Blog'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'UTC'
DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('Pelican', 'http://getpelican.com/'),
         ('Python.org', 'http://python.org/'),
         ('Jinja2', 'http://jinja.pocoo.org/'),)

# Social widget
SOCIAL = (('You can add links in your config file', '#'),
          ('Another social link', '#'),)

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
`;
}

function createPublishConfig() {
  return `#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

# This file is only used if you use "make publish" or
# explicitly specify it as your config file.

import os
import sys
sys.path.append(os.curdir)
from pelicanconf import *

# If your site is available via HTTPS, make sure SITEURL begins with https://
SITEURL = ''
RELATIVE_URLS = False

FEED_ALL_ATOM = 'feeds/all.atom.xml'
CATEGORY_FEED_ATOM = 'feeds/{slug}.atom.xml'

DELETE_OUTPUT_DIRECTORY = True

# Following items are often useful when publishing

#DISQUS_SITENAME = ""
#GOOGLE_ANALYTICS = ""
`;
}

// Image handling functions (unchanged)
async function handleImages(request, env, corsHeaders, pathname) {
  const user = await authenticateRequest(request);
  if (!user || !user.isAdmin) {
    return new Response(JSON.stringify({ error: 'Admin access required' }), {
      status: 403,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  if (request.method === 'POST' && pathname === '/images/upload') {
    return await uploadImage(request, env, corsHeaders, user.userId);
  } else if (request.method === 'GET' && pathname.startsWith('/images/')) {
    const imagePath = pathname.substring(8); // Remove '/images/'
    return await getImage(env, corsHeaders, imagePath);
  }

  return new Response('Method not allowed', { status: 405, headers: corsHeaders });
}

async function uploadImage(request, env, corsHeaders, userId) {
  const formData = await request.formData();
  const file = formData.get('image');

  if (!file) {
    return new Response(JSON.stringify({ error: 'No image file provided' }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  const filename = `${userId}/${Date.now()}_${file.name}`;
  
  try {
    await env.BUCKET.put(filename, file.stream(), {
      httpMetadata: {
        contentType: file.type,
      },
    });

    const imageUrl = `/images/${filename}`;

    return new Response(JSON.stringify({
      url: imageUrl,
      path: filename
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to upload image' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

async function getImage(env, corsHeaders, imagePath) {
  try {
    const object = await env.BUCKET.get(imagePath);
    
    if (!object) {
      return new Response('Image not found', { status: 404, headers: corsHeaders });
    }

    return new Response(object.body, {
      headers: {
        ...corsHeaders,
        'Content-Type': object.httpMetadata?.contentType || 'application/octet-stream',
        'Cache-Control': 'public, max-age=31536000',
      },
    });
  } catch (error) {
    return new Response('Failed to fetch image', { status: 500, headers: corsHeaders });
  }
}

// Refresh endpoint (existing functionality)
async function handleRefresh(request, env, corsHeaders) {
  const url = new URL(request.url);
  const providedKey = url.searchParams.get('key');
  const secretKey = env.REFRESH_SECRET_KEY;
  const deployHookUrl = env.DEPLOY_HOOK_URL;

  if (!providedKey || providedKey !== secretKey) {
    return new Response('Unauthorized', { status: 401, headers: corsHeaders });
  }

  const deployResponse = await fetch(deployHookUrl, {
    method: "POST"
  });

  if (deployResponse.ok) {
    return new Response('✅ Blog rebuild triggered!', { status: 200, headers: corsHeaders });
  } else {
    return new Response('⚠️ Failed to trigger rebuild.', { status: 500, headers: corsHeaders });
  }
}

// Helper functions
async function authenticateRequest(request) {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }

  try {
    const token = authHeader.substring(7);
    const payload = JSON.parse(atob(token));

    if (payload.exp < Date.now()) {
      return null;
    }

    return {
      userId: payload.userId,
      email: payload.email,
      isAdmin: payload.isAdmin
    };
  } catch (error) {
    return null;
  }
}

function generateId() {
  return 'post_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
} 