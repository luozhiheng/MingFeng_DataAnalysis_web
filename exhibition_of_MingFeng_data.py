# coding=utf-8
# import datetime
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdate
import pandas as pd
import numpy as np
# import re
from MingFeng_DataAnalysis_Report.readdata import date_interval
from MingFeng_DataAnalysis_Report import formula as formula
# from MingFeng_DataAnalysis_Report.formula import nominal_capacity

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pd.set_option('display.max_colwidth', 1000)
pd.set_option('mode.chained_assignment', None)  # 设置SettingWithCopyWarning
# plt.rcParams['font.sans-serif'] = ['simhei']  # 指定默认字体
# plt.rcParams['axes.unicode_minus'] = False  # 解决负号变方块问题
color = ['b', 'r', 'g', 'y', 'c', 'm', '#FFFFCC', '#663300', '#66CC00', '#99CCCC']  # 绘图色谱
path = BASE_DIR + "\MingFeng_DataAnalysis_Report\concat_dataset.csv"
dt = pd.read_csv(path, index_col=0, encoding='GBK')  # 若要正确显示graph，请让date_ascol=0


# fill_datetime_interval,为对数据预处理
def fill_datetime_interval(dt):
    '''
    由于部分数据缺失，导致日期不连续（5min 间隔），故需以0/NaT填充
    :param dt:
    :return:
    '''
    dt = dt.sort_values(by=[dt.columns[0]])
    dt = dt.dropna()
    # print('after sort date::\r\n%s'%dt.index)
    # print('generated data\r\n')
    dt.index = pd.to_datetime(dt.loc[:, dt.columns[0]])
    # print('let col0 == dt index:\r\n %s'%dt.index)
    # print(dt.head())
    # print('\r\nafter reindex freq=5min:\r\n')
    dt = dt.reindex(pd.date_range(dt.index[0], dt.index[-1], freq='5T'))
    dt.loc[:, dt.columns[0]] = dt.index
    # print(dt.index)
    # print('make index become num %s')
    dt = dt.rename(dict(zip(dt.index, list(range(len(dt.index))))), axis='index')
    # print(dt.index)
    dt = dt.fillna(pd.NaT)  # *******若填充为0，则polt出来的图不好看
    return dt


dt = fill_datetime_interval(dt)
# print(dt)
'''
1.bug1:某台主机的回水温度探头存在静态误差，找出该台主机，并查看是否已修复
'''


def showbug_TemBiased(dt_input, search='冷冻水', freq=12):
    '''
    显示四台主机的冷冻/冷却回水温度
    :param dt_input:
    :param search:
    :param freq:
        freq默认是2h
    :return:
    '''
    dates_result1 = date_interval(dt_input, freq)
    dates1 = dates_result1[0]  # x轴的时间序列
    step1 = dates_result1[1]  # 时间间隔的步长
    # ax = plt.subplot(111)
    # legend_list = []
    # for i in range(4):
    #     power = 'CH{}功率(KW)'.format(i + 1)  # CH的功率列名
    #     col_temp = [col for col in dt_input.columns if re.match('CH' + str(i + 1) + search + '回水温度', col) is not None]
    #     dt_analysis = dt_input.loc[:, col_temp]
    #     t, = ax.plot(dt_analysis, label=col_temp[0])
    #     legend_list.append(t)
    # ax.xaxis.set_major_formatter(mdate.DateFormatter('%Y/%m/%d %H:%M:%S'))  # 设置时间标签显示格式
    # plt.xticks(list(np.arange(0, dt_input.index[-1], step1)), tuple(dates1), rotation=30)  # x轴的时间间隔设置
    # plt.grid()
    # ax.legend(handles=legend_list)
    # plt.show()


# showbug_TemBiased(dt,freq=24)

'''
2.显示主机进回水温差，看之前的预处理（例如除去冷冻水进水温度小于冷冻水出水温度的偏差情况）是否有效
'''


def show_temp_4ax(dt_in, search='冷冻水', freq=6):
    '''
    同时显示4台主机的水温
    :param dt_in:
        传入的数据
    :param search:
        search可以是冷冻水或者冷却水
    :param freq:
        freq默认是2h
    :return:
    '''
    dates_result1 = date_interval(dt_in, freq)
    dates1 = dates_result1[0]  # x轴的时间序列
    step1 = dates_result1[1]  # 时间间隔的步长
    # for i in range(4):
    #     legend_list = []
    #     col_temp = [col for col in dt_in.columns if re.match('CH' + str(i + 1) + search + '.{2}温度', col) is not None]
    #     data_temp = dt_in.loc[:, col_temp]
    #     ax = plt.subplot(2, 2, i + 1)
    #     t1, = ax.plot(data_temp.loc[:, data_temp.columns[0]], label=col_temp[0])
    #     t2, = ax.plot(data_temp.loc[:, data_temp.columns[1]], label=col_temp[1])
    #     legend_list.append(t1)
    #     legend_list.append(t2)
    #     ax.legend(handles=[t1, t2])
    #     plt.grid()
    #     if i + 1 > 2:
    #         plt.xticks(list(np.arange(0, dt_in.index[-1], step1)), tuple(dates1), rotation=30)  # x轴的时间间隔设置
    # plt.show()


# show_temp_4ax(dt)

'''
3.求解原有主机的温度相关模型
'''


# 显示主机的COP
def show_COP(dt_in, chillerid=4, freq=12):
    dates_result1 = date_interval(dt_in, freq)
    dates1 = dates_result1[0]  # x轴的时间序列
    step1 = dates_result1[1]  # 时间间隔的步长
    col_chwST_T = 'CH{}冷冻水出水温度(℃)'.format(chillerid)
    col_chwRT_T = 'CH{}冷冻水回水温度(℃)'.format(chillerid)
    col_chflow = 'CH{}冷冻水出水流量(m^3/h)'.format(chillerid)
    col_power = 'CH{}功率(KW)'.format(chillerid)
    # 计算冷量、cop
    capacity = 1000 * 4.186 * (dt_in.loc[:, col_chwRT_T] - dt_in.loc[:, col_chwST_T]) * dt_in.loc[:, col_chflow] / 3600
    capacity[capacity < 10] = 0
    cop = capacity.div(dt_in.loc[:, col_power])
    cop[cop == np.inf] = pd.NaT
    cop[cop == 0] = pd.NaT
    # 绘图
    # ax = plt.subplot()
    # # fig=plt.subplot(212)#再画一条功率、冷量线
    # plt.xticks(list(np.arange(0, dt_in.index[-1], step1)), tuple(dates1), rotation=50)  # x轴的时间间隔设置
    # ax2 = ax.twinx()
    # # ax2_fig=fig.twinx()#再画一条功率、冷量线
    # cop_line = ax.scatter(x=cop.index, y=cop, s=20, marker="*", label='CH{} COP'.format(chillerid))
    # chwST_T_line, = ax2.plot(dt_in.loc[:, col_chwST_T], color='m', label=col_chwST_T)
    # # power_line,=fig.plot(dt_in.loc[:,col_power],color='c',label=col_power)#再画一条功率、冷量线
    # # capacity_line,=ax2_fig.plot(capacity,label='CH{}冷量（kw）'.format(chillerid))#再画一条功率、冷量线
    # ax.set_ylabel('CH{} COP'.format(chillerid))
    # ax2.set_ylabel(col_chwST_T)
    # ax.legend(handles=[cop_line, chwST_T_line])
    # # fig.legend(handles=[power_line,capacity_line])#再画一条功率、冷量线
    # ax.grid()
    # # fig.grid()再画一条功率、冷量线
    # plt.show()


# show_COP(dt)

# 求α=(1/COP+1-(T_cwRT/T_chwST ))Q_evap
def show_alpha_regressionline(dt_in, chillerid=1):
    # 温度相关模型的数据集要过滤，采用功率大于120kw的作为基准集
    dt_in = dt_in.loc[dt_in['CH{}功率(KW)'.format(chillerid)] > 120, :]
    # alpha值及回归线求解
    t_cw_rt = dt_in.loc[:, 'CH{}冷却水进水温度(℃)'.format(chillerid)] + 273.15  # ℃要转为K
    t_chw_st = dt_in.loc[:, 'CH{}冷冻水出水温度(℃)'.format(chillerid)] + 273.15  # ℃要转为K
    t_ratio = t_cw_rt / t_chw_st
    alpha, slope, intercept, results_a = formula.cal_alpha_a2_intercept(dt_in, chillerid)
    x = np.array([min(t_ratio), max(t_ratio)])
    y = intercept + x * slope
    # print('alpha result:\r\n%s\r\n' % results_a.summary())
    # # print('\r\n intercept:%s  slope:%s  R_Squared:%s'%(intercept,slope,r2))
    # # 绘散点图
    # fig = plt.subplot()
    # plt.title('alpha 对(T_cwRT/T_chwST )的函数')
    # alpha_line = fig.scatter(t_ratio, alpha, s=20, label='alpha')
    # regression_line, = fig.plot(x, y, label='alpha对温度比率回归线', color='red')
    # fig.legend(handles=[alpha_line, regression_line])
    # plt.show()


# show_alpha_regressionline(dt, 1)


# 求β=(1/COP+1-(T_cwRT/T_chwST ))Q_evap+A_2(T_cwRT/T_chwST)
def show_beta_regressionline(dt_in, chillerid=1):
    # 温度相关模型的数据集要过滤，采用功率大于120kw的作为基准集
    dt_in = dt_in.loc[dt_in['CH{}功率(KW)'.format(chillerid)] > 120, :]
    t_cw_rt = dt_in.loc[:, 'CH{}冷却水进水温度(℃)'.format(chillerid)] + 273.15
    t_chw_st = dt_in.loc[:, 'CH{}冷冻水出水温度(℃)'.format(chillerid)] + 273.15
    t_ratio = t_cw_rt / t_chw_st  # ℃要转为K
    # 计算beta
    beta, intercept, slope, results_b = formula.cal_beta_a0_a1(dt_in, chillerid)
    # beta回归线求解
    x = np.array([min(t_cw_rt), max(t_cw_rt)])
    y = intercept + x * slope
    # print('beta result:\r\n%s\r\n' % results_b.summary())
    # # 绘beta回归线
    # fig = plt.subplot()
    # beta_line = fig.scatter(t_cw_rt, beta, s=20, label='beta')
    # beta_regressionline = fig.plot(x, y, label='beta对t_cw_rt回归线', color='red')
    # plt.legend()
    # plt.title('beta对冷却回水温度的函数')
    # plt.show()


# show_beta_regressionline(dt,1)

# 温度相关模型
def t_dependence_model(dt_in, chillerid=1):
    # print(dt_in.iloc[:,].head())
    t_cw_rt = np.arange(28., 32., 1)
    load_percent = np.arange(0.4, 1.01, 0.01)
    color = ['b', 'r', 'g', 'y', 'c', 'm', '#FFFFCC', '#663300', '#66CC00', '#99CCCC']
    # 定4℃冷冻水出水绘图,定7℃冷冻水出水绘图
    # fig1 = plt.figure('fig1')
    # fig2 = plt.figure('fig2')
    # for t_chw, fig in zip([4, 7], [fig1, fig2]):
    #     ax1 = fig.add_subplot(111)
    #     ax1.set_title('定{}℃设定冷冻水出水，CH{}机组性能'.format(t_chw, chillerid))
    #     for cw, c in zip(t_cw_rt, color[:len(t_cw_rt)]):
    #         cop_reciprocal = formula.cal_t_dependence_model(dt_in, chillerid, [cw] * len(load_percent),
    #                                                         [t_chw] * len(load_percent),
    #                                                         load_percent * nominal_capacity)
    #         ax1.plot(load_percent, 1 / cop_reciprocal, color=c, label='恒定冷却水{}℃'.format(cw))
    #     ax1.grid()
    #     ax1.legend()
    # plt.show()


# t_dependence_model(dt)

'''
4.求解新系统制冷量输出量、原系统主机模拟用电量
'''


def show_system_capacity(dt_in, freq=48):
    dates_result1 = date_interval(dt_in, freq)
    dates1 = dates_result1[0]  # x轴的时间序列
    step1 = dates_result1[1]  # 时间间隔的步长
    # 计算系统负荷
    system_capacity = formula.cal_system_capacity(dt_in)
    # 计算原系统模拟用电量/COP
    power_sum, cop = formula.cal_simulated_power(dt_in, 1, dt_in['冷却水管出水温度(℃)'], dt_in['冷供水管供水温度(℃)'], system_capacity)
    # 绘图，系统负荷/模拟用电
    # fig = plt.subplot()
    # plt.xticks(list(np.arange(0, dt_in.index[-1], step1)), tuple(dates1), rotation=30)  # x轴的时间间隔设置
    # fig2 = fig.twinx()
    # sys_cap_line, = fig.plot(system_capacity / 3.517, label='系统负荷分布')
    # pow_sum_line, = fig.plot(power_sum, color=color[2], label='CH1主机模拟用电')
    # cop_line = fig2.scatter(cop.index, cop, s=1, color=color[1], label='主机模拟COP')
    # fig.set_ylabel('负荷需求（RT）、功率（kw）')
    # fig2.set_ylabel('COP')
    # plt.title('2017年9-12月 系统负荷、模拟用电、COP分布')
    # plt.legend(handles=[sys_cap_line, pow_sum_line, cop_line])
    # plt.grid()
    # plt.show()


# show_system_capacity(dt)


def show_electricity_consumption_diff(dt_in, freq=8, p="true"):
    dates_result1 = date_interval(dt_in, freq)
    dates1 = dates_result1[0]  # x轴的时间序列
    step1 = dates_result1[1]  # 时间间隔的步长
    # 计算系统负荷
    system_capacity = formula.cal_system_capacity(dt_in)
    # 计算原系统模拟用电量/COP
    power_simulate, cop = formula.cal_simulated_power(dt_in, 1, dt_in['冷却水管出水温度(℃)'], dt_in['冷供水管供水温度(℃)'],
                                                      system_capacity)
    # 计算新系统主机+蓄冷泵用电量
    power_retrofit = 0
    for i in range(1, 5):
        power_retrofit += dt_in['CH{}功率(KW)'.format(i)]
    power_retrofit += dt_in['KAP6功率(KW)']
    # 计算原系统、新系统电费
    electric_charge_simulate = formula.cal_electric_charge(dt_in, power_simulate, group='day')
    electric_charge_retrofit = formula.cal_electric_charge(dt_in, power_retrofit, group='day')
    # print('原系统主机累计电费：%s\r\n新系统主机+蓄冷泵累计电费：%s' % (electric_charge_simulate, electric_charge_retrofit))
    # print('power_simulate %s\r\n power_retrofit %s' % (power_simulate, power_retrofit))
    print("cal again,check if cache work")
    if p == "fales":
        pass
        # 绘图
        # fig = plt.subplot()
        # plt.xticks(list(np.arange(0, dt_in.index[-1], step1)), tuple(dates1), rotation=30)  # x轴的时间间隔设置
        # fig.plot(power_simulate, color=color[5], label='原系统模拟主机用电')
        # fig.plot(power_retrofit, label='新系统主机+蓄冷泵用电')
        # fig.set_title('新旧系统用电对比')
        # fig.set_ylabel('功率（kw）')
        # fig.grid()
        # fig.legend()
        # plt.show()
    else:
        return [power_simulate, power_retrofit, dates1, electric_charge_simulate, electric_charge_retrofit]


# show_electricity_consumption_diff(dt)

'''
5.冷却水泵没有与主机连锁、同时变频器也没发挥应有的作用
'''


def show_equip_power(dt_in, freq=8):
    dates_result1 = date_interval(dt_in, freq)
    dates1 = dates_result1[0]  # x轴的时间序列
    step1 = dates_result1[1]  # 时间间隔的步长
    power_chiller = 0
    for i in range(1, 5):
        power_chiller += dt_in['CH{}功率(KW)'.format(i)]
    power_cooling = dt_in['KAP2功率(KW)'] + dt_in['KAP4功率(KW)']
    power_cooled = dt_in['KAP1功率(KW)'] + dt_in['KAP5功率(KW)']
    # fig = plt.subplot()
    # plt.xticks(list(np.arange(0, dt_in.index[-1], step1)), tuple(dates1), rotation=30)  # x轴的时间间隔设置
    # fig.plot(power_chiller, label='主机功率（kw）')
    # fig.plot(power_cooling, color=color[2], label='冷却水泵功率（kw）')
    # fig.plot(power_cooled, color=color[5], label='冷冻水泵功率（kw）')
    # fig.set_title('各设备用电功率')
    # fig.set_ylabel('功率（kw）')
    # fig.grid()
    # fig.legend()
    # plt.show()


# show_equip_power(dt)


'''
6.蓄冷量的设定值分析
'''


def show_storage_analysis(dt_in, freq=48):
    dates_result1 = date_interval(dt_in, freq)
    dates1 = dates_result1[0]  # x轴的时间序列
    step1 = dates_result1[1]  # 时间间隔的步长
    # 计算系统负荷
    system_capacity = formula.cal_system_capacity(dt_in)
    # 计算蓄放冷量
    storage_capacity = 4.186 * 1000 * (dt_in['蓄冷槽进水温度(℃)'] - dt_in['蓄冷槽出水温度(℃)']) * dt_in['蓄冷槽出水流量(m^3/h)'] / 3600
    # 绘图，系统负荷/蓄冷量
    # fig = plt.subplot()
    # plt.xticks(list(np.arange(0, dt_in.index[-1], step1)), tuple(dates1), rotation=30)  # x轴的时间间隔设置
    # 计算累计蓄冷量、放冷量
    storage_sum = 0
    position_start = 0
    sign_pre = None  # 指示蓄冷还是放冷
    sign_get = True  # 指示是否取符号
    for sc, i, t in zip(storage_capacity, storage_capacity.index, dt_in['时   间']):
        # 把蓄放冷量较小值置0
        if -50 < sc < 50:
            sc = 0
            storage_capacity[i] = 0
        # 放置放冷量值的标签
        if not np.isnan(sc):
            # 第一次获得符号
            if sign_get:
                position_start = i
                sign_pre = formula.sign(sc)
                sign_get = False
                print('第一次获得符号%s' % sc)
            # 已获得符号，则比较下一次是否和上一次符号相同,增加累计置
            elif (sc > 0 and sign_pre == '+') or (sc < 0 and sign_pre == '-'):
                print('符号相同%s' % sc)
                storage_sum += sc * 5 / 60
            # sc==0,则可以打印累计结果
            elif sc == 0:
                print('打印结果%s' % sc)
                position_height = 100
                position_between = (i + position_start) / 2
                if -50 < storage_sum < 50:
                    position_height = 200
                if storage_sum > 0:
                    # fig.text(position_between, position_height, '累计放冷量为：%s' % np.round(storage_sum / 3.517))
                    storage_sum = 0
                elif storage_sum < 0:
                    # fig.text(position_between, -position_height, '累计蓄冷量为：%s' % -np.round(storage_sum / 3.517))
                    storage_sum = 0
                sign_get = True  # 打印结果后重置sign_pre，继续寻找第一个符号
            # 否则符号是直接变号了，可以打印累计结果
            else:
                print('打印结果%s' % sc)
                position_height = 100
                position_between = (i + position_start) / 2
                if -50 < storage_sum < 50:
                    position_height = 200
                if storage_sum > 0:
                    # fig.text(position_between, position_height, '累计放冷量为：%s' % np.round(storage_sum / 3.517))
                    storage_sum = 0
                elif storage_sum < 0:
                    # fig.text(position_between, -position_height, '累计蓄冷量为：%s' % -np.round(storage_sum / 3.517))
                    storage_sum = 0
                sign_pre = formula.sign(sc)  # 打印结果后重置sign_pre，继续寻找第一个符号
    # 注释/绘图
    # plt.text(len(dt_in) / 4, 1500, '注释：对于蓄放冷量，大于0为放冷，小于0为蓄冷')
    # # sys_cap_line, = fig.plot(system_capacity / 3.517, label='系统负荷分布')
    # storage_line, = fig.plot(storage_capacity / 3.517, color=color[2], label='蓄放冷量')
    # fig.fill_between(storage_capacity.index, storage_capacity / 3.517, 0, where=storage_capacity > 0, facecolors='blue')
    # fig.fill_between(storage_capacity.index, storage_capacity / 3.517, 0, where=storage_capacity < 0,
    #                  facecolors=color[2])
    # fig.set_ylabel('冷量（RT）')
    # plt.title('2017年9-12月 蓄放冷量分布')
    # plt.legend()
    # plt.grid()
    # plt.show()

# show_storage_analysis(dt, 1)
