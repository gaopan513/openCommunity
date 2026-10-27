/**
 * 经验问答模块 API
 */
import request from '@/utils/request'

/** 获取问题列表 */
export function getQuestions(params) {
  return request.get('/questions/', { params })
}

/** 获取问题详情 */
export function getQuestion(id) {
  return request.get(`/questions/${id}/`)
}

/** 提问 */
export function createQuestion(data) {
  return request.post('/questions/', data)
}

/** 删除问题 */
export function deleteQuestion(id) {
  return request.delete(`/questions/${id}/`)
}

/** 回答问题 */
export function addAnswer(id, data) {
  return request.post(`/questions/${id}/answer/`, data)
}

/** 采纳回答 */
export function acceptAnswer(id, answerId) {
  return request.put(`/questions/${id}/accept/`, { answer_id: answerId })
}

/** 点赞问题 */
export function likeQuestion(id) {
  return request.post(`/questions/${id}/like/`)
}

/** 点赞/取消点赞回答 */
export function likeAnswer(questionId, answerId) {
  return request.post(`/questions/${questionId}/answers/${answerId}/like/`)
}
