from django.http import HttpResponse
from django.shortcuts import render
import exhibition_of_MingFeng_data as mf
import MingFeng_DataAnalysis_Report.formula as formula
import os
import pandas as pd
import json


# Create your views here.
def index(request):
    return render(request, "index.html")


def home_graph(request):
    # 模拟用电对比
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = base_dir + "\MingFeng_DataAnalysis_Report\concat_dataset.csv"
    dt = pd.read_csv(path, index_col=0, encoding='GBK')  # 若要正确显示graph，请让date_ascol=0
    dt = dt.dropna()
    dt = dt.sort_values(by=['时   间'])
    consume_result = mf.show_electricity_consumption_diff(dt)
    power_simulate1 = formula.pd2json(consume_result[0], '模拟用电')
    power_retrofit1 = formula.pd2json(consume_result[1], '实际用电')
    consume_result1 = [power_simulate1, power_retrofit1, consume_result[2], json.dumps(consume_result[3]),
                       json.dumps(consume_result[4])]
    return HttpResponse(
        '{0}({1})'.format(request.GET["callback"], json.dumps(consume_result1)),
        content_type='application/x-javascript')


def detail_home(request):
    return render(request, "exhibition/detail_home.html")


def overview_chiller(request):
    return render(request, "exhibition/overview_chiller.html")
