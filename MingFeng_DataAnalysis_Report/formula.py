#! usr/bin/python
# coding=utf-8

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import datetime
import re

nominal_capacity = 319 * 3.517  # CH1螺杆机名义制冷量
price_peak = 1.4703  # 峰段电价
price_normal = 0.6862  # 平段电价
price_valley = 0.369  # 谷段电价


def cal_chiller_para(dt, chillerid, want='cop', with_time=False):
    """
        计算冷机的冷量或者COP

    :param dt:输入的数据集

    :param chillerid:主机的编号

    :param want: 'cop'是cop，'cap'是冷量

    :param with_time 是否返回带有时间序列的dataframe


    """
    col_chwST_T = 'CH{}冷冻水出水温度(℃)'.format(chillerid)
    col_chwRT_T = 'CH{}冷冻水回水温度(℃)'.format(chillerid)
    col_chflow = 'CH{}冷冻水出水流量(m^3/h)'.format(chillerid)
    col_power = 'CH{}功率(KW)'.format(chillerid)
    # 计算冷量、cop
    capacity = 1000 * 4.186 * (dt.loc[:, col_chwRT_T] - dt.loc[:, col_chwST_T]) * dt.loc[:, col_chflow] / 3600
    capacity[capacity < 10] = 0
    cop = capacity.div(dt.loc[:, col_power])
    cop[cop == np.inf] = pd.NaT
    cop[cop == 0] = pd.NaT
    if want == 'cop':
        if with_time:
            return pd.DataFrame({'cop': cop, '时   间': dt['时   间']})
        else:
            return cop
    elif want == 'cap':
        if with_time:
            return pd.DataFrame({'capacity': capacity, '时   间': dt['时   间']})
        else:
            return capacity
    else:
        print('parameter--want only accept "cop" or "cap"')


def cal_alpha_a2_intercept(dt_in, chillerid):
    t_cw_rt = dt_in.loc[:, 'CH{}冷却水进水温度(℃)'.format(chillerid)] + 273.15  # ℃要转为K
    t_chw_st = dt_in.loc[:, 'CH{}冷冻水出水温度(℃)'.format(chillerid)] + 273.15
    t_ratio = t_cw_rt / t_chw_st
    cop = cal_chiller_para(dt_in, chillerid, want='cop')
    capacity = cal_chiller_para(dt_in, chillerid, want='cap')
    alpha = ((1 / cop) + 1 - t_ratio) * capacity
    # alpha回归线求解
    alpha2t_ratio = pd.DataFrame({'t_ratio': t_ratio, 'alpha': alpha})
    results = smf.ols('alpha~t_ratio', alpha2t_ratio).fit()
    intercept, slope = results.params
    a2 = slope
    return alpha, a2, intercept, results


def cal_beta_a0_a1(dt_in, chillerid):
    t_cw_rt = dt_in.loc[:, 'CH{}冷却水进水温度(℃)'.format(chillerid)] + 273.15
    t_chw_st = dt_in.loc[:, 'CH{}冷冻水出水温度(℃)'.format(chillerid)] + 273.15  # ℃要转为K
    t_ratio = t_cw_rt / t_chw_st
    alpha, a_2, intercept_a, results_a = cal_alpha_a2_intercept(dt_in, chillerid)
    # beta 回归线求解
    beta = alpha + a_2 * t_ratio
    beta_t_cw_rt_df = pd.DataFrame({'beta': beta, 't_cw_rt': t_cw_rt})
    results = smf.ols('beta~t_cw_rt', beta_t_cw_rt_df).fit()
    intercept, slope = results.params
    a_0 = intercept
    a_1 = slope
    return beta, a_0, a_1, results


def cal_t_dependence_model(dt_in, chillerid, t_cw_rt, t_chw_st, evaporator_load):
    # 数据检查
    if len(t_cw_rt) != len(t_chw_st) and len(t_cw_rt) != len(evaporator_load):
        raise Warning("t_cw_rt:len %s, t_chw_st:len %s, evaporator_load:len %s ,长度不一" % (
            len(t_cw_rt), len(t_chw_st), len(evaporator_load)))
    # 温度相关模型的数据集要过滤，采用功率大于120kw的作为基准集
    dt_in = dt_in.loc[dt_in['CH{}功率(KW)'.format(chillerid)] > 120, :]
    t_cw_rt = np.array(t_cw_rt) + 273.15  # ℃要转为K，不要改动此种表示方式（不要用t_cw_rt+273.15）
    t_chw_st = np.array(t_chw_st) + 273.15  # ℃要转为K
    t_ratio = t_cw_rt / t_chw_st
    alpha, a_2, intercept_a, result_a = cal_alpha_a2_intercept(dt_in, chillerid)
    beta, a_0, a_1, result_b = cal_beta_a0_a1(dt_in, chillerid)
    cop_reciprocal = -1 + t_ratio + (
            a_0 + a_1 * t_cw_rt - a_2 * t_ratio) / evaporator_load  # evaporator_load
    #  是一个制冷量kw,ASHRAE 的公式有误，a_0前是正号
    # print('a0:%s  a1:%s a2:%s'%(a_0,a_1,a_2))
    return cop_reciprocal


def cal_system_capacity(dt_in):
    ch_sum_capacity = cal_chiller_para(dt_in, 1, want='cap', with_time=True)  # 主机1对系统输出冷量
    for i in [3, 4]:
        ch_capacity = cal_chiller_para(dt_in, i, want='cap', with_time=True)  # 主机3和4对系统输出冷量
        index_h02h8 = time_selector(ch_capacity)
        ch_capacity['capacity'].iloc[index_h02h8] = 0
        ch_sum_capacity['capacity'] += ch_capacity['capacity']
    ch_sum_capacity = ch_sum_capacity['capacity']  # 只要冷量值的column
    storage_capacity = 4.186 * 1000 * (dt_in['蓄冷槽进水温度(℃)'] - dt_in['蓄冷槽出水温度(℃)']) * dt_in['蓄冷槽出水流量(m^3/h)'] / 3600
    storage_capacity[storage_capacity < 0] = 0  # 留下放冷量的值，<0为蓄冷量
    system_capacity = ch_sum_capacity + storage_capacity
    return system_capacity


def cal_simulated_power(dt_in, chillerid, t_cw_rt, t_chw_st, evaporator_load):
    """

    :param dt_in:

    :param chillerid: 主机的编号

    :param t_cw_rt: 这里用冷却水主管进水温度，传入的是一个serial

    :param t_chw_st: 这里用冷冻水主管供水温度，传入的是一个serial

    :param evaporator_load: 这里用系统负荷，传入的是一个serial

    :return: power_sum:返回模拟用电量
    """
    # 计算开启的主机数量/load/COP
    num_start = np.ceil(evaporator_load / nominal_capacity)
    capacity_each_chiller = evaporator_load / num_start
    cop_reciprocal = cal_t_dependence_model(dt_in, chillerid, t_cw_rt, t_chw_st, capacity_each_chiller)
    power_sum = capacity_each_chiller * cop_reciprocal * num_start
    return power_sum, 1 / cop_reciprocal


def cal_electric_charge(dt_in, power_consumption, group='all'):
    """
    :argument 按峰谷电价计算电费，默认数据的间隔为5min

    :param dt_in:

    :param power_consumption: 每5min的耗电功率

    :return: 累计电费
    """
    if group == 'all':
        electric_charge = 0
    else:
        electric_charge = {}
    dt_in = dt_in.dropna()
    for t, power in zip(dt_in['时   间'], power_consumption):
        t = datetime.datetime.strptime(str(t), "%Y-%m-%d %H:%M:%S")
        if np.isnan(power):
            power = 0
        hour = t.hour
        if (9 <= hour < 12) or (19 <= hour < 22):
            price = power * price_peak * 5 / 60
        elif (8 <= hour < 9) or (12 <= hour < 19) or (22 <= hour < 24):
            price = power * price_normal * 5 / 60
        elif (0 <= hour < 8):
            price = power * price_valley * 5 / 60
        else:
            raise ValueError('可能是数据集的时间列数据出问题了！')
        if group == 'day':
            tmonth = '0{0}'.format(t.month) if t.month < 10 else t.month
            tday = '0{0}'.format(t.day) if t.day < 10 else t.day
            if '{0}-{1}-{2}'.format(t.year, tmonth, tday) in electric_charge:
                electric_charge['{0}-{1}-{2}'.format(t.year, tmonth, tday)] += price
            else:
                electric_charge['{0}-{1}-{2}'.format(t.year, tmonth, tday)] = 0
        else:
            electric_charge += price
    if group == 'day':  ##统计完，按时间排序
        electric_charge = [(k, electric_charge[k]) for k in sorted(electric_charge.keys())]
    return electric_charge


def time_selector(dt_in, ):  # TODO 这里的功能应该是输入开始、结束时间然后返回
    index_t = []
    dt_in = dt_in.dropna()
    for t, i in zip(dt_in['时   间'], dt_in.index):
        t = datetime.datetime.strptime(str(t), "%Y-%m-%d %H:%M:%S")
        if t.hour < 8:
            index_t.append(i)
        if t.hour == 8 and t.minute <= 35:
            index_t.append(i)
    return index_t


def sign(sc):
    if sc > 0:
        sign_pre = '+'
    elif sc == 0:
        sign_pre = '0'
    else:
        sign_pre = '-'
    return sign_pre


def pd2json(serial, title):
    result = "{{\"{0}\":[\"".format(title)
    list1 = serial.tolist()
    result += "\",\"".join(map(str, list1))
    result = "{0}\"]}}".format(result)
    return result


def pd_time_group(time, group='day'):
    if group == 'day':
        sptime = re.match(r'(\d{4}-\d{2}-\d{2})', time)
        if sptime:
            sptime = sptime.group(1)
            return sptime
        else:
            raise ValueError('传入时间{0}格式不正确'.format(sptime))
