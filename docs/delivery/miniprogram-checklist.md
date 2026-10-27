# 微信小程序端联调核对清单

> 对应 [miniprogram-plan.md](../planning/miniprogram-plan.md) MP7/MP8 阶段。
> 以 `frontend/src/api/*.js` 的函数全集为基准核对小程序端覆盖情况；
> 每项联调需在微信开发者工具 + 真机各过一遍。

## 一、接口联调对照表

标记说明：✅ 已实现待联调｜➖ 本期不做（Web 端职责）。

### auth（miniprogram/src/api/auth.js）
| 函数 | 后端端点 | 小程序调用处 | 状态 |
|---|---|---|---|
| wechatLogin | POST /api/v1/auth/wechat-login/ | stores/user.loginByWechat（App 冷启、登录页） | ✅ |
| debugLogin | POST /api/v1/auth/debug-login/ | stores/user.loginByWechatTest（登录页「本地测试登录」，仅开发构建显示） | ✅（旁路） |
| logout | POST /api/v1/auth/logout/ | stores/user.logout | ✅ |
| getProfile | GET /api/v1/users/profile/ | pages/profile onShow | ✅ |
| updateProfile | PUT /api/v1/users/profile/ | pages/profile 保存资料；头像经 multipart PUT 同端点 | ✅ |

### discussion
| 函数 | 后端端点 | 调用处 | 状态 |
|---|---|---|---|
| getPosts | GET /posts/?post_type&search&ordering&page | posts/list | ✅ |
| getPost | GET /posts/{id}/ | posts/detail | ✅ |
| createPost | POST /posts/（multipart 多 images） | posts/create【R1 spike 场景①】 | ✅ |
| updatePost | PATCH /posts/{id}/ | 本期无编辑入口，预留 | ✅（未接线） |
| deletePost | DELETE /posts/{id}/ | posts/detail（本人） | ✅ |
| likePost | POST /posts/{id}/like/ | 列表卡片 + 详情 | ✅ |
| addComment | POST /posts/{id}/comments/ {content,parent} | posts/detail（楼层+楼中楼） | ✅ |
| featurePost | PUT /posts/{id}/feature/ | ➖ 管理员功能留 Web | ➖ |

### qa
| 函数 | 后端端点 | 调用处 | 状态 |
|---|---|---|---|
| getQuestions | GET /questions/?is_solved&search&tag&ordering | qa/list | ✅ |
| getQuestion | GET /questions/{id}/ | qa/detail | ✅ |
| createQuestion | POST /questions/ {title,content,tags[]} | qa/create | ✅ |
| deleteQuestion | DELETE /questions/{id}/ | qa/detail（本人） | ✅ |
| addAnswer | POST /questions/{id}/answer/ | qa/detail 输入条 | ✅ |
| acceptAnswer | PUT /questions/{id}/accept/ {answer_id} | qa/detail（提问者且未解决） | ✅ |
| likeQuestion | POST /questions/{id}/like/ | qa/detail | ✅ |

### secondhand
| 函数 | 后端端点 | 调用处 | 状态 |
|---|---|---|---|
| getProducts | GET /products/?category&status&condition&search&ordering | products/list | ✅ |
| getMyProducts | GET /products/?mine=1（后端按登录用户过滤 seller） | products/mine | ✅ |
| getProduct | GET /products/{id}/ | products/detail、create-edit 回填 | ✅ |
| createProduct | POST /products/（multipart ≤9 images） | products/create-edit【R1 spike 场景②】 | ✅ |
| updateProduct | PATCH /products/{id}/（传 images 即全量替换） | products/create-edit 编辑模式 | ✅ |
| deleteProduct | DELETE /products/{id}/ | products/detail（本人卖家） | ✅ |
| changeProductStatus | PUT /products/{id}/status/ {status} | products/detail 卖家操作区（状态机映射） | ✅ |
| addProductComment | POST /products/{id}/comments/ | products/detail | ✅ |
| getProductCategories | GET /product-categories/ | products/list、create-edit | ✅ |

✅ 已完成：后端 `ProductViewSet` 已支持 `?mine=1` 过滤参数（未登录返回空集），"我的商品"页改为单页请求 + 分页加载（原客户端过滤方案已移除）。

### merchants（居民视角裁剪版）
| 函数 | 后端端点 | 调用处 | 状态 |
|---|---|---|---|
| getMerchants | GET /merchants/?category&search | services/index 商家段 | ✅ |
| getMerchant | GET /merchants/{id}/ | merchants/detail | ✅ |
| getMerchantActivities | GET /merchants/{id}/activities/ | merchants/detail（失败回退详情内嵌 activities） | ✅ |
| getMerchantReviews | GET /merchants/{id}/reviews/ | 本期使用详情内嵌 reviews，预留分页加载 | ✅（未接线） |
| addMerchantReview | POST /merchants/{id}/reviews/ {rating,content} | merchants/detail 底部弹层 | ✅ |
| getMerchantCategories | GET /merchant-categories/ | services/index | ✅ |
| applyMerchant / getMyShop / updateMyShop / auditMerchant / createActivity / updateActivity / deleteActivity / replyMerchantReview | ➖ 商家侧与管理侧能力，留 Web 端 | ➖ | ➖ |

### housekeeping（居民视角）
| 函数 | 后端端点 | 调用处 | 状态 |
|---|---|---|---|
| getServiceCategories | GET /housekeeping/categories/ | services/index 家政段 | ✅ |
| getProviders | GET /housekeeping/providers/?category(slug)&search | services/index 家政段 | ✅ |
| getProvider | GET /housekeeping/providers/{id}/ | housekeeping/detail | ✅ |
| createBooking | POST /housekeeping/bookings/ {service_item,preferred_date,preferred_time,remark} | housekeeping/detail 预约弹层（日期 ≥ 今天前端预校验） | ✅ |
| getBookings | GET /housekeeping/bookings/?status&page | bookings/my（并发补齐分页） | ✅ |
| updateBooking | PUT /housekeeping/bookings/{id}/ | bookings/my 改期（仅 pending 可改，前后端双校验） | ✅ |
| updateBookingStatus | PUT /housekeeping/bookings/{id}/status/ {cancelled} | bookings/my 取消（pending/confirmed 两态合法取消） | ✅ |
| addBookingReview | POST /housekeeping/bookings/{id}/review/ {rating,content} | bookings/my 评价弹层（completed 后） | ✅ |
| applyProvider / auditProvider | ➖ 服务商入驻与审核留 Web | ➖ | ➖ |

### admin（居民视角裁剪版）
| 函数 | 后端端点 | 调用处 | 状态 |
|---|---|---|---|
| getAnnouncements | GET /announcements/ | pages/home 公告区 | ✅ |
| getStatistics / createReport | ➖ 管理员/举报管理留 Web | ➖ | ➖ |

## 二、关键专项验证

| 项 | 内容 | 结果记录 |
|---|---|---|
| R1 多图 spike-① | 发帖选 3 张图发布 → 详情回显图序正确 → Django media 目录落盘 `media/posts/YYYYMM/` | ☐ 开发者工具 ☐ 真机 |
| R1 多图 spike-② | 商品发布 9 张图 → 编辑保留 9 张 → 替换其中 3 张 → 详情仍 9 张且新旧正确 | ☐ |
| 本地测试登录 | 无真实 AppID 时点登录页「本地测试登录」→ 自动创建 resident 并返回 JWT → 跳转首页 | ☐ |
| 单图头像 | profile 选头像 → multipart PUT → 头像立即生效并同步 store 缓存 | ☐ |
| 401 刷新链路 | 手动把 Storage 中 access_token 改为垃圾值 → 任意请求 → 自动刷新重放成功且 storage 双 token 更新 | ☐ |
| 踢出链路 | refresh_token 改为垃圾值 → 请求 → 清三键 + reLaunch 登录页带 redirect | ☐ |
| 游客边界 | 未登录浏览列表/详情正常；点赞/评论/预约/发帖弹「需要登录」 | ☐ |
| token 并存 | Web 与小程序同时登录同一操作流互不干扰（两套独立 refresh 会话） | ☐ |
| 媒体域名 | 图片 URL（相对路径 mediaUrl 补全）在真机可加载（合法域名/HTTPS） | ☐ |

## 三、MP8 发布合规清单

- ☐ 注册小程序账号，将 AppID 写入 `miniprogram/src/manifest.json` 的 `mp-weixin.appid`
- ☐ 微信公众平台配置 **request / uploadFile / downloadFile 合法域名**（与 Web 同域的 HTTPS 地址）
- ☐ `.env.production` 的 `VITE_API_BASE_URL` 改为线上地址后重新 `npm run build:mp-weixin`
- ☐ 后端设置 `WECHAT_MINIAPP_APPID / WECHAT_MINIAPP_SECRET` 环境变量（本地开发可用「本地测试登录」旁路 `debug-login` 代替，该接口仅 `DEBUG=True` 可用、上线自动失效）
- ☐ 后台完善《用户隐私保护指引》（收集头像/昵称用途声明），已开启 `__usePrivacyCheck__`；发帖/商品选图用到的 `chooseMedia` 须额外声明「收集你选中的照片或视频信息」（用摄像头则加「访问你的摄像头」），未声明会报 `errno 112`
- ☐ 类目选择：生活服务 / 社区服务相关类目，按要求补充资质材料
- ☐ tabBar 图标为开发期占位（文字圆角标），提审前替换为正式设计图标（96×96 PNG）
- ☐ 体验版全量走查第二节专项验证表后再提交审核

## 四、已知限制（本期接受）

1. Web 密码账号与微信账号为两个独立身份（计划 R2）；后续可加「绑定已有账号」。
2. 我的商品为客户端过滤（接口缺 seller 参数），数据量大时有截断可能。
3. 图片上传使用手工 multipart 报文方案，若真机出现兼容问题按计划启用备选评审路线。
4. 商家评价仅展示详情内嵌最近 5 条，翻页入口待后续接入 reviews 分页接口。
5. 选图（`chooseMedia`）在后台未声明「照片或视频」隐私权限时，开发者工具/真机均报 `errno 112`，无法调起相册；本地联调需先在公众平台完善《用户隐私保护指引》（见第三节清单）。
