#! usr/bin/python
# coding=utf-8
import pandas as pd
import os
import re

# 如果直接修改pandas读取的数据集会出现SettingWithCopyWarning警告，对其设为不警告
pd.set_option('mode.chained_assignment', None)
pd.set_option('display.max_colwidth', 1000)


def find_file(path):
    '''
    查找目标路径中的xlsx文件
    :param path:
    :return:
        root：找到含有"报表"的xlsx文件所在的目录
        files：文件名的list
    '''
    for root, dirs, files in os.walk(path):
        if re.match('报表.+\.xlsx|csv', files[0]) != None:
            break
    # print(files)
    if re.match('.+\.xlsx|csv', files[0]) == None:
        raise FileNotFoundError('Don\'t find any xlsx/csv file in the path:%s' % path)
    return root, files


def __getChiller(i):
    """
        定义出主机的column,chillers[0]表示ch1的list

    :parameter
        i:是chiller的编号

    :return
        返回一个包含某主机column的list
    """
    chillers = ['#我是占位的#']
    for x in range(1, 5):
        ch_col = [u'CH{}冷冻水出水温度(℃)'.format(x), u'CH{}冷冻水回水温度(℃)'.format(x), u'CH{}冷冻水出水流量(m^3/h)'.format(x),
                  u'CH{}冷却水进水温度(℃)'.format(x), u'CH{}冷却水出水温度(℃)'.format(x), u'CH{}功率(KW)'.format(x),
                  u'CH{}电量(KWh)'.format(x)]
        chillers.append(ch_col)
    return chillers[i]


def __value_temp_modify(dt):
    """
        对于主机冷冻水出水温度/冷却水回水温度 > 冷冻水回水温度/冷却水出水温度的值置0，因为这是不符合常理的；注意这里是直接修改输入的数据集
    :param
        dt: 输入的数据集

    """
    for i in range(1, 5):
        # 处理冷冻水温度的修正
        ch_col = __getChiller(i)
        value_chw = dt.loc[dt[ch_col[0]] > dt[ch_col[1]], ch_col[1]]
        dt.loc[dt[ch_col[0]] > dt[ch_col[1]], ch_col[0]] = value_chw
        # print('*********value_ch%s\r\n%s'%(i,dt.loc[:,ch_col[:2]]))

        # 处理冷却水温度的修正
        value_cw = dt.loc[dt[ch_col[3]] > dt[ch_col[4]], ch_col[4]]
        dt.loc[dt[ch_col[3]] > dt[ch_col[4]], ch_col[3]] = value_cw


def __value_pow_modify(dt):
    """
        将功率小于1kw的值置0；注意这里是直接修改输入的数据集
    :param
        dt: 输入数据集

    """
    for i in range(1, 5):
        ch_col = __getChiller(i)
        dt.loc[dt[ch_col[5]] < 5, ch_col[5]] = 0


def date_interval(dt, hour_freq, record_interval=5):
    """

    :param hour_freq: 想要显示的x轴的时间间隔
    :param record_interval: 这是原始数据的记录间隔，默认5min
    :return: 日期的list
    """
    step = 60 / record_interval
    freq = step * hour_freq
    dates = [d for d, i in zip(dt['时   间'], dt['时   间'].index) if (i - 1) % freq == 0]  # 此处设置x轴时间的间隔
    return (dates, freq)


def __getdata(path, date_ascol=0, dropna=1, temp_modify=1, power_modify=1):
    """
        读取1个数据集，默认丢掉数据集中有NA值的行，对温度、功率，某些数据影响了后面绘的图的美观，建议修正
    :param
        date_ascol:默认使用编号为index，date_ascol为1则日期做为index
    :param
        path: 读取的数据集的路径。注意：文件为utf-8编码的csv文件
    :param
        dropna:默认丢掉数据集中的NA值的行
    :param
        temp_modify:对于主机冷冻水出水温度/冷却水回水温度 > 冷冻水回水温度/冷却水出水温度的值置0，因为这是不符合常理的
    :param
        power_modify:将功率小于1kw的值置0；
    :return:
        返回数据集
    """
    dateset = None
    if date_ascol == 0:
        dateset = pd.read_csv(path, encoding=u'utf-8', index_col=u'编号(单位)')
    if date_ascol == 1:
        dateset = pd.read_csv(path, encoding=u'utf-8', index_col=u'时   间', parse_dates=True)
        dateset = dateset.drop(columns=u'编号(单位)')
        # dateindex = pd.to_datetime(dataset['时   间'], format='%Y-%m-%d %H:%M:%S')  # 得到time series 类型的datetime
        # length = list([d for d in dateindex]).__len__()  # 这是时间序列的长度
        # index_list = dict(zip(range(1, length + 1), list([d for d in dateindex])))  # 把时间序列转成dict
        # dt = dataset.drop(columns='时   间')  # 去除时间的一列,或者通过da=dataset.loc[:,list(dataset.columns[1:])]来去除时间一列
        # datedt = dt.rename(index_list)  # 因为原来的编号是int型，要变成其他类型需要用rename，其中rename的参数是一个dict
        # #print(datedt.head())  # 测试通过
    mydt = dateset
    if dropna == 1:
        mydt = dateset.dropna(how='any')
    if temp_modify == 1:
        __value_temp_modify(mydt)
    if power_modify == 1:
        __value_pow_modify(mydt)
    return mydt


def getdata(path, date_ascol=0, dropna=1, temp_modify=1, power_modify=1):
    """
        读取多个数据，默认丢掉数据集中有NA值的行，对温度、功率，某些数据影响了后面绘的图的美观，建议修正
    :param
        date_ascol:默认使用编号为index，date_ascol为1则日期做为index
    :param
        path: 读取的数据集的路径。注意：文件为utf-8编码的csv文件
    :param
        dropna:默认丢掉数据集中的NA值的行
    :param
        temp_modify:对于主机冷冻水出水温度/冷却水回水温度 > 冷冻水回水温度/冷却水出水温度的值置0，因为这是不符合常理的
    :param
        power_modify:将功率小于1kw的值置0；
    :return:
        返回数据集
    """
    root, files = find_file(path)
    # files=sorted(files,key = lambda i:int(re.match(r'(\d+)',i).group()))#这里的排序未完成，读取文件时顺序不一定按时间排序，但如果在这里先排序，则容易导致最后结果不对。
    # 例如文件1的时间包含了文件2 的时间。故在最后合并了整个dataframe之后再按时间排序
    dataset = None
    dataset_concat = None
    for filename in files:
        # if filename == files[2]:#这里为了快速测试，不用加载所有文件
        #     break
        file = root + '\\' + filename
        if date_ascol == 0:
            dataset = pd.read_excel(file, skiprows=2, skip_footer=1, index_col=0)
        else:
            dataset = pd.read_excel(file, skiprows=2, skip_footer=1, index_col=1)
            dataset.drop(columns=u'编号', inplace=True)
            '''# dateindex = pd.to_datetime(dataset['时   间'], format='%Y-%m-%d %H:%M:%S')  # 得到time series 类型的datetime
            # length = list([d for d in dateindex]).__len__()  # 这是时间序列的长度
            # index_list = dict(zip(range(1, length + 1), list([d for d in dateindex])))  # 把时间序列转成dict
            # dt = dataset.drop(columns='时   间')  # 去除时间的一列,或者通过da=dataset.loc[:,list(dataset.columns[1:])]来去除时间一列
            # datedt = dt.rename(index_list)  # 因为原来的编号是int型，要变成其他类型需要用rename，其中rename的参数是一个dict
            # #print(datedt.head())  # 测试通过'''
        print('loaded file:%s' % filename)
        dataset_concat = pd.concat([dataset, dataset_concat], ignore_index=True)
    dataset_concat.fillna('/', inplace=True)
    print('\r\n**************\r\ndealing with dataframe concat\r\n************\r\n')
    dataset_concat.columns = map(
        lambda x, y: x + '(' + y + ')' if y != '/' and dataset_concat.index[0] != pd.NaT else x,
        list(dataset_concat.columns), list(dataset_concat.iloc[0]))  # 把单位拼接到columns中
    if date_ascol == 0:  # 重要：文件拼接时末尾与另一文件开始存留了单位行（要除去）
        row_todelete = [indexnum for indexnum in dataset_concat.loc[dataset_concat['CH3功率(KW)'].isin(['KW'])].index]
        dataset_concat.drop(row_todelete, inplace=True)
    else:
        dataset_concat.drop(dataset_concat.index[0], inplace=True)
    mydt = dataset_concat
    print('\r\n**************\r\ndealing with sorting and data washing\r\n**************\r\n')
    if dropna == 1:
        mydt = dataset_concat.dropna(how='any')
    if date_ascol == 0:  #
        mydt.sort_values('时   间', inplace=True)
        mydt = mydt.reindex(list(range(len(mydt.index))))  # reindex需要在dropna的后面，请不要移动顺序
    else:
        mydt.sort_index(axis=0, inplace=True)
        assert mydt.index[0] < mydt.index[-50], 'index{} is not < index{}'.format(0, -50)  # 只是为了检查排序的效果
    if temp_modify == 1:
        __value_temp_modify(mydt)
    if power_modify == 1:
        __value_pow_modify(mydt)
    print('load completed')
    # print(mydt.index)
    return mydt


def __save_dataset(save_path):
    '''
    把merge后的dataset保存
    :param save_path:
    :return:
    '''
    dataset = getdata(r"C:\Users\HASEE\Desktop\MingFeng-Analysis\DataSource")
    dataset.to_csv(save_path, encoding=u'GBK')

# __save_dataset('concat_dataset.csv')
