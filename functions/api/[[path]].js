/* export async function onRequest(context) {
  const { request, params } = context;
  const url = new URL(request.url);

  // 你的 Flask 后端地址（HTTP 即可，服务端到服务端不受混合内容限制）
  const BACKEND = "http://42.193.173.200:5173";

  // 拼接后端路径：/api/xxx → http://42.193.173.200:5173/api/xxx
  const backendUrl = BACKEND + url.pathname + url.search;

  // 转发原始请求（保留 method、headers、body）
  const modifiedRequest = new Request(backendUrl, request);

  // 为了绕过某些后端对 Host 头的校验，可以显式设置
  modifiedRequest.headers.set("Host", "42.193.173.200:5173");

  return fetch(modifiedRequest);
} */






export async function onRequest(context) {
  const url = new URL(context.request.url);
  
  // 把这里换成你后端的 HTTPS 地址（隧道域名或 Nginx 配了证书的域名）
  const BACKEND = "http://42.193.173.200:5173";
  
  const targetUrl = BACKEND + url.pathname + url.search;
  
  const response = await fetch(targetUrl, {
    method: context.request.method,
    headers: context.request.headers,
    body: ["GET", "HEAD"].includes(context.request.method) 
      ? null 
      : context.request.body,
  });
  
  // 把后端响应原样返回给浏览器
  return new Response(response.body, {
    status: response.status,
    headers: response.headers,
  });
}