# -*- coding:utf-8 -*-
import re

import torch
import torch.nn.functional as F
from django.shortcuts import render
from util.pre_load import segment, neo4jconn, model_dict, name_dict, category_dict

model, words, classes, index_classes = model_dict
model.eval()

actor_name_dict, movie_name_dict = name_dict[0], name_dict[1]

def question_answering(request):
	context = {'ctx':''}
	if(request.GET):
		question = request.GET['question']
		#question = question[:300]
		# 移除空格
		question = question.strip()
		question = question.lower()

		word_nature = segment.seg(question)
		print('word_nature:{}'.format(word_nature))
		pattern = [
			[r"^.\w+兽药检出的种类个数", ],
			[r"\w+兽药检出的频次是多少", ],
			[r"^.\w+兽药检出毒性情况", ],
			[r"\w+兽药种类检出情况", ],
			[r"^.\w+兽药残留水平", ],
		]

		pos = -1
		classfication_num = -1
		for i in range(len(pattern)):
			for x in pattern[i]:
				index = re.search(x, question)
				if (index):
					pos = index.span()[0]
					classfication_num = i
					break
			if (pos != -1):
				break


		if classfication_num == 0:
			word = ''
			cnt_time = 0
			cnt_type = 0
			for term in word_nature:
				if str(term.nature) == 'ns':
					city = term.word
				elif str(term.nature) == 'm':
					if cnt_time == 0:
						start = term.word
					elif cnt_time == 1:
						end = term.word
					cnt_time = cnt_time + 1
				elif str(term.nature) == 'n':
					if cnt_type == 0:
						type = term.word
					cnt_type = cnt_time + 1

			if word == '':
				ret_dict = []
			ret_dict = neo4jconn.veterinary_rate(city, start, end)

		elif classfication_num == 1:
			word = ''
			cnt_time = 0
			cnt_type = 0
			for term in word_nature:
				if str(term.nature) == 'ns':
					city = term.word
				elif str(term.nature) == 'm':
					if cnt_time == 0:
						start = term.word
					elif cnt_time == 1:
						end = term.word
					cnt_time = cnt_time + 1
				elif str(term.nature) == 'n':
					if cnt_type == 0:
						type = term.word
					cnt_type = cnt_time + 1
			if word == '':
				ret_dict = []

			ret_dict = neo4jconn.veterinary_kind(city, start, end)
		elif classfication_num == 2:
			word = ''
			cnt_time = 0
			cnt_type = 0
			for term in word_nature:
				if str(term.nature) == 'ns':
					city = term.word
				elif str(term.nature) == 'm':
					if cnt_time == 0:
						start = term.word
					elif cnt_time == 1:
						end = term.word
					cnt_time = cnt_time + 1
				elif str(term.nature) == 'n':
					if cnt_type == 0:
						type = term.word
					cnt_type = cnt_time + 1
			if word == '':
				ret_dict = []

			ret_dict = neo4jconn.veterinary_tox2(city, start, end,type)


		elif classfication_num == 3:
			word = ''
			cnt_time = 0
			cnt_type = 0
			for term in word_nature:
				if str(term.nature) == 'ns':
					city = term.word
				elif str(term.nature) == 'm':
					if cnt_time == 0:
						start = term.word
					elif cnt_time == 1:
						end = term.word
					cnt_time = cnt_time + 1
				elif str(term.nature) == 'n':
					if cnt_type == 0:
						type = term.word
					cnt_type = cnt_time + 1
			if word == '':
				ret_dict = []

			ret_dict = neo4jconn.veterinary_tox(city, start, end,type)

		elif classfication_num == 4:
			word = ''
			cnt_time = 0
			cnt_type = 0
			for term in word_nature:
				if str(term.nature) == 'ns':
					city = term.word
				elif str(term.nature) == 'm':
					if cnt_time == 0:
						start = term.word
					elif cnt_time == 1:
						end = term.word
					cnt_time = cnt_time + 1
				elif str(term.nature) == 'n':
					if cnt_type == 0:
						type = term.word
					cnt_type = cnt_time + 1
			if word == '':
				ret_dict = []

			ret_dict = neo4jconn.veterinary_res(city, start, end,type)






		if(len(ret_dict)!=0):
			return render(request,'question_answering.html',{'ret':ret_dict})

		return render(request, 'question_answering.html', {'ctx':'暂未找到答案'})

	return render(request, 'question_answering.html', context)


# 分词，需要将电影名，演员名和评分数字转为nm，nnt，ng
def _sentence_segment(word_nature):

	sentence_words = []
	for term in word_nature:
		if str(term.nature) == 'nnt':
			sentence_words.append('nnt')
		elif str(term.nature) == 'nm':
			sentence_words.append('nm')
		elif str(term.nature) == 'ng':
			sentence_words.append('ng')
		elif str(term.nature) == 'm':
			sentence_words.append('x')
		else:
			sentence_words.append(term.word)
	return sentence_words


def _bow(word_nature, show_detail=True):
	sentence_words = _sentence_segment(word_nature)
	# 词袋
	bag = [0] * len(words)
	for s in sentence_words:
		for i, w in enumerate(words):
			if w == s:
				bag[i] = 1  # 词在词典中
			if show_detail:
				print("found in bag:{}".format(w))
	return [bag]


def _predict_class(word_nature):
	sentence_bag = _bow(word_nature, False)
	with torch.no_grad():
		outputs = model(torch.FloatTensor(sentence_bag))
	#print('outputs:{}'.format(outputs))
	predicted_prob, predicted_index = torch.max(F.softmax(outputs, 1), 1)  # 预测最大类别的概率与索引
	#print('softmax_prob:{}'.format(predicted_prob))
	#print('softmax_index:{}'.format(predicted_index))
	results = []
	# results.append({'intent': index_classes[predicted_index.detach().numpy()[0]], 'prob': predicted_prob.detach().numpy()[0]})
	results.append({'intent': predicted_index.detach().numpy()[0], 'prob': predicted_prob.detach().numpy()[0]})
	#print('result:{}'.format(results))
	return results


def _get_response(predict_result):
	tag = predict_result[0]['intent']
	return tag


def chatbot_response(word_nature):
	predict_result = _predict_class(word_nature)
	res = _get_response(predict_result)
	return res
def chatbot_response_z(word_nature):
	#predict_result = _predict_class(word_nature)
	for i in word_nature:
		if i == '兽药':
			tag = 1
			break
	res = tag
	return 1