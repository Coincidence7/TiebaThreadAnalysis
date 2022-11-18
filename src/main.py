import os
import time

from Spider.Spider import Spider
from src.Spider.TiebaThread import TiebaThread
import jieba.analyse
import numpy as np
import re
from wordcloud import WordCloud, ImageColorGenerator
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib import colors
import jieba.analyse
import pandas as pd
from snownlp import SnowNLP
from jieba import lcut
from gensim.similarities import SparseMatrixSimilarity
from gensim.corpora import Dictionary
from gensim.models import TfidfModel

HTMLS_PATH = '../htmls/'
TIEBA_JIEBTA_DICT = '../dict/tieba-dict.txt'

TEST_HTML_PATH = '../htmls/threads/pg1_北京工业大学.html'

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
STOP_WORDS_FILE_PATH = '停用词.txt'

#找到中文
def find_chinese(file):
    pattern = re.compile(r'[^\u4e00-\u9fa5]')
    chinese = re.sub(pattern, '', file)
    return chinese
#读取txt,转成列表
def read_txt_similarity():
    f = open("TiebaData.txt",'rt',encoding='utf-8')
    txt_list = f.readlines()
    txt_list = [x.strip() for x in txt_list]
    txt_list = [x for x in txt_list if len(x)>0]
    txt_list = [find_chinese(x) for x in txt_list]
    txt_list = [x for x in txt_list if len(x)>0]
    return txt_list

def read_txt():
    f = open("TiebaData.txt",'rt',encoding='utf-8')
    txt_list = f.readlines()
    txt_list = [x.strip() for x in txt_list]
    txt_list = [x for x in txt_list if len(x)>0]
    txt_list = [x for x in txt_list if x!="楼主："]
    txt_list = [x for x in txt_list if x!="评论："]
    txt_list = [find_chinese(x) for x in txt_list if x!="评论："]
    txt_list = [x for x in txt_list if len(x)>0]

    return txt_list
#列表转字典，帖子作为关键字，评论作为键值
def list_dict(txt_list):
    index_=[]
    dict_data={}
    for i in range(len(txt_list)):
        if txt_list[i]=="楼主":
            index_.append(i)
    for x in range(1,len(index_)-1):
        a=(index_[x])
        b=(index_[x-1])
        dantiao=txt_list[b:a]
        dict_data[dantiao[1]]=dantiao[3:]
    return dict_data

def similarities(keyword,texts):
    req_list =[]
    # 分词
    texts = [lcut(text) for text in texts]
    # 2、基于文本集建立词典，并获得词典特征数
    dictionary = Dictionary(texts)
    num_features = len(dictionary.token2id)
    # 基于词典，将分词列表集转换成稀疏向量集，称作语料库
    corpus = [dictionary.doc2bow(text) for text in texts]
    # 同理，把基础文本也要转成向量集
    kw_vector = dictionary.doc2bow(lcut(keyword))
    # 创建TF-IDF模型，训练语料库
    tfidf = TfidfModel(corpus)
    # 用训练好的模型处理比对文本和基础文本
    tf_texts = tfidf[corpus]
    tf_kw = tfidf[kw_vector]
    # 相似度计算
    sparse_matrix = SparseMatrixSimilarity(tf_texts, num_features)
    similarities = sparse_matrix.get_similarities(tf_kw)
    #输出相似度
    for e, s in enumerate(similarities, 1):
        req_list.append(s)
    return req_list

def print_similarities():
    txt_list_similarity = read_txt_similarity()
    dict_data = list_dict(txt_list_similarity)
    res_list = []
    for key in dict_data.keys():
        tiezi_list = len(dict_data[key]) * [key]
        pinglun_list = dict_data[key]
        req_list = similarities(key, dict_data[key])
        res_list.extend(list(zip(tiezi_list, pinglun_list, req_list)))
    df = pd.DataFrame(res_list)
    df.columns = ['帖子', '评论', '相关度']
    df.to_csv("帖子评论相关度分析.csv", encoding="utf_8", index=False)

    res1_list = []
    for key in dict_data.keys():
        if len(dict_data[key]) >= 2:
            keyword = dict_data[key][0]
            texts = dict_data[key][1:]
            tiezi = len(texts) * [key]
            jichu = len(texts) * [keyword]
            req_list = similarities(key, dict_data[key])
            res1_list.extend(list(zip(tiezi, jichu, texts, req_list)))
    df = pd.DataFrame(res1_list)
    df.columns = ['帖子', '基础语句', "评论", '相关度']
    df.to_csv("评论与评论相关度分析.csv", encoding="utf_8", index=False)

    print("相似度已输出至.csv文件")


def draw_cloud(txt_list):

    t = "".join(txt_list)
    jieba.analyse.set_stop_words(STOP_WORDS_FILE_PATH)
    keywords_count_list = jieba.analyse.textrank(t, topK=100, withWeight=True)
    image = Image.open("base.jpg")  # 作为背景轮廓图
    graph = np.array(image)
    color_list=['#DC143C', '#00FF7F', '#FF6347', '#8B008B', '#00FFFF', '#0000FF', '#8B0000', '#FF8C00',
            '#1E90FF', '#00FF00', '#FFD700', '#008080', '#008B8B', '#8A2BE2', '#228B22', '#FA8072', '#808080']
    colormap=colors.ListedColormap(color_list)

    wc = WordCloud(font_path='simkai.ttf', background_color='white', max_words=100,colormap=colormap, random_state = 30,mask=graph)
    # wc = WordCloud(font_path='simkai.ttf', background_color='white', max_words=100, random_state = 30,mask=graph)
    frequencies_dic={}
    for key_word in keywords_count_list:
        frequencies_dic[key_word[0]] = key_word[1]
    print(frequencies_dic)
    wc.generate_from_frequencies(frequencies_dic)  # 根据给定词频生成词云
    image_color = ImageColorGenerator(graph)
    plt.imshow(wc)
    plt.axis("off")  # 不显示坐标轴
    plt.show()
    wc.to_file('词云.jpg')  # 图片命名

def emotion(txt_list):
    emotion_List = []
    s_list = []
    for txt in txt_list:
        s = SnowNLP(txt).sentiments
        s_list.append(s)
        if s >= 0.53:
            emotion_List.append("积极")
        elif s <= 0.47:
            emotion_List.append("消极")
        else:
            emotion_List.append("中性")
    df = pd.DataFrame()
    df['文本'] = txt_list
    df['情感指数'] = s_list
    df['情感'] = emotion_List
    df.to_csv("感.csv", index=False)
    x = ['积极', '中性', '消极']
    y = []
    for em in x:
        y.append(emotion_List.count(em))
    d_list = [i/sum(y)*100 for i in y]
    plt.pie(d_list,explode=None,labels=x, autopct='%1.2f%%',startangle=200,counterclock=False)
    plt.title("情感占比分布")
    plt.savefig("情感占比分布.jpg")
    plt.show()


if __name__ == '__main__':
    txt_list = read_txt()
    draw_cloud(txt_list)
    emotion(txt_list)
    print_similarities()

    # tieba_name = '北京工业大学'
    #
    # # 手动为词典增加贴吧相关用词 提升切割的精准度
    # jieba.load_userdict(TIEBA_JIEBTA_DICT)
    # jieba.add_word(tieba_name + '吧')
    #
    # spider = Spider(tieba_name)
    #
    # # 待爬取页数
    # target_pages = [1]
    #
    # # spider.load_page(TEST_HTML_PATH, 1)
    # spider.retrieve_page(target_pages)
    # spider.save_page(HTMLS_PATH, target_pages)
    #
    # # 按帖子获取全部内容
    # threads = spider.get_threads()
    # print(threads)
    #
    # print('\n' + '*' * 40 + '\n')
    #
    # cur_page = 0
    # for p in threads:
    #     cur_page += 1
    #     for t in p[(2 if cur_page == 1 else 0):]:
    #         print('-' * 40 + '\n' + t[0][1])
    #         time.sleep(1)
    #         new_thread = TiebaThread(t[0][0], t[0][1])
    #         new_thread.retrieve_thread()
    #         new_thread.save_thread()
    #         rep = new_thread.get_replies()
    #
    #         print(rep)
    #         # fileName = 'TiebaData.txt'
    #         # with open(fileName, 'a', encoding='utf-8') as file:
    #         #     for i in range(len(rep)):
    #         #         file.write(rep[i]+"\n")
    #
    #         print(new_thread.get_segments())
    #         print(new_thread.get_key_words())

