/**
 * 小程序上传工具
 *
 * - uploadMultipart: 手工构造 multipart/form-data 报文（ArrayBuffer），一次请求
 *   携带多个同名 images 文件字段，对应后端 DRF ListField(child=ImageField) 的多图契约。
 *   （uni.request / wx.request 的 data 仅支持 string/object/ArrayBuffer，
 *    不支持 FormData，因此必须手工拼 ArrayBuffer 报文）
 *   401 时复用 request.js 的静默刷新后重放一次，语义与普通请求一致。
 *   提交前按后端 validate_image 规则预检单张大小（≤5MB），避免整包上传后才失败。
 */
import { BASE_URL, toast, refreshAccessToken, clearAuthAndGoLogin } from '@/utils/request'

/** UTF-8 字符串转 ArrayBuffer（兼容中文） */
function str2ab(str) {
  const encoded = unescape(encodeURIComponent(str))
  const bytes = []
  for (let i = 0; i < encoded.length; i++) {
    bytes.push(encoded.charCodeAt(i))
  }
  return new Uint8Array(bytes).buffer
}

/** ArrayBuffer 拼接 */
function concatBuffers(buffers) {
  const total = buffers.reduce((sum, b) => sum + (b ? b.byteLength : 0), 0)
  const merged = new Uint8Array(total)
  let offset = 0
  for (const buf of buffers) {
    if (buf) {
      merged.set(new Uint8Array(buf), offset)
      offset += buf.byteLength
    }
  }
  return merged.buffer
}

/** Promise 化读取本地临时文件内容 */
function readFile(filePath) {
  return new Promise((resolve, reject) => {
    uni.getFileSystemManager().readFile({
      filePath,
      success: (res) => resolve(res.data),
      fail: reject,
    })
  })
}

/** 读取文件大小（字节）；失败返回 -1 表示跳过预检 */
function getFileSize(filePath) {
  return new Promise((resolve) => {
    // getFileInfo 已废弃，改用 FileSystemManager.getFileInfo
    uni.getFileSystemManager().getFileInfo({
      filePath,
      success: (res) => resolve(res.size),
      fail: () => resolve(-1),
    })
  })
}

/** 允许的图片格式（对齐后端 validate_image：jpg/jpeg/png/webp），并用于推导 multipart 部件 Content-Type */
const IMAGE_MIME_MAP = {
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  png: 'image/png',
  webp: 'image/webp',
}

/**
 * 多文件 + 文本字段一次性提交（用于发帖 / 商品发布与编辑）
 *
 * @param {Object} options
 * @param {string} options.url - 接口路径（如 '/posts/'、'/products/{id}/'）
 * @param {string} [options.method='POST'] - POST 创建 / PATCH 编辑（images 全量替换语义）
 * @param {Object} [options.fields] - 文本字段（title/content/tags 等）
 * @param {Array<{path:string, type?:string}>} [options.files] - 图片临时路径列表
 * @param {string} [options.name='images'] - 文件字段名，须与后端 ListField 一致
 * @param {boolean} [options.retried=false] - 401 是否已重放（内部用）
 * @returns {Promise<object>} 后端统一信封 {code,message,data}
 */
export async function uploadMultipart({
  url,
  method = 'POST',
  fields = {},
  files = [],
  name = 'images',
  retried = false,
}) {
  if (!files.length) {
    // 无图片时退化为普通 JSON 请求，避免空 multipart
    const { default: request } = await import('@/utils/request')
    const body = { ...fields }
    delete body.images
    return request[method.toLowerCase()](url, body)
  }

  const boundary = `----opencommunity${Date.now()}${Math.floor(Math.random() * 1e6)}`
  const dashes = `--${boundary}\r\n`
  const parts = []

  // 文本字段段
  for (const [key, value] of Object.entries(fields)) {
    if (value === undefined || value === null) continue
    parts.push(str2ab(`${dashes}Content-Disposition: form-data; name="${key}"\r\n\r\n${value}\r\n`))
  }

  // 文件段：多个同名字段即数组（与 Web 端 FormData.append('images', f) 等价）
  for (let i = 0; i < files.length; i++) {
    const file = typeof files[i] === 'string' ? { path: files[i] } : files[i]
    // 预检单张大小（对齐后端 validate_image ≤5MB），避免整包读完才被后端拒绝
    const size = await getFileSize(file.path)
    if (size > 5 * 1024 * 1024) {
      toast(`第 ${i + 1} 张图片超过 5MB，请压缩后重试`)
      throw new Error('image too large')
    }
    // 按扩展名预检格式（对齐后端 validate_image 白名单），并推导部件 Content-Type
    const segs = file.path.split('.')
    const ext = segs.length > 1 ? segs.pop().toLowerCase() : 'jpg'
    const mime = IMAGE_MIME_MAP[ext]
    if (!mime) {
      toast(`第 ${i + 1} 张图片格式不支持，仅支持 jpg/png/webp`)
      throw new Error('unsupported image format')
    }
    const filename = file.name || `img${i}.${ext}`
    parts.push(
      str2ab(
        `${dashes}Content-Disposition: form-data; name="${name}"; filename="${filename}"\r\n` +
          `Content-Type: ${mime}\r\n\r\n`
      )
    )
    const data = await readFile(file.path)
    parts.push(data)
    parts.push(str2ab('\r\n'))
  }
  parts.push(str2ab(`--${boundary}--\r\n`))

  const data = concatBuffers(parts)

  const token = uni.getStorageSync('access_token')
  const header = { 'content-type': `multipart/form-data; boundary=${boundary}` }
  if (token) header.Authorization = `Bearer ${token}`

  let res
  try {
    res = await new Promise((resolve, reject) => {
      uni.request({
        url: url.startsWith('http') ? url : BASE_URL + url,
        method,
        data,
        header,
        timeout: 60000,
        success: resolve,
        fail: reject,
      })
    })
  } catch (e) {
    // fail 分支：网络不通/超时
    console.error('[uploadMultipart] request fail:', e)
    toast('网络连接失败，请检查网络')
    throw new Error('network error')
  }

  let body = res.data
  if (typeof body === 'string') {
    try {
      body = JSON.parse(body)
    } catch {
      /* 保持原样走错误分支 */
    }
  }

  // 401：token 过期，静默刷新后重放一次（与 request.js 语义对齐）
  if (res.statusCode === 401) {
    if (!retried && uni.getStorageSync('refresh_token')) {
      try {
        await refreshAccessToken()
        return uploadMultipart({ url, method, fields, files, name, retried: true })
      } catch (e) {
        // 网络错误（uni.request fail 带 errMsg）不判定会话失效，弱网下避免误踢登录
        if (e && e.errMsg) toast('网络连接失败，请检查网络')
        else clearAuthAndGoLogin()
        throw Object.assign(new Error('上传失败'), { statusCode: 401, data: body })
      }
    }
    // 无 refresh token 或重放后仍 401：会话失效
    clearAuthAndGoLogin()
    throw Object.assign(new Error('登录已过期'), { statusCode: 401, data: body })
  }

  if (res.statusCode >= 200 && res.statusCode < 300 && body && body.code === 0) {
    return body
  }
  const message = (body && body.message) || '上传失败，请重试'
  toast(message)
  throw Object.assign(new Error(message), { statusCode: res.statusCode, data: body })
}
