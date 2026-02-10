import pandas as pd
from statsmodels.tsa.filters.hp_filter import hpfilter
from tkinter import Tk, filedialog, messagebox, simpledialog
import os

# 定义一个安全转换日期的函数，忽略非日期字符串
def safe_convert_to_datetime(col, date_format=None):
    # 试图根据格式转换日期，如果失败则忽略错误
    result_col = pd.to_datetime(col, format=date_format, errors='coerce')
    return result_col.dt.strftime('%Y-%m-%d') if date_format else result_col

import numpy as np
import statsmodels.tsa.stattools as ts
import math
import logging

def BoostedHP(x, lam=1600, iter=True, stopping="BIC", \
              sig_p=0.050, Max_Iter=100):
    x = np.array(x)

    ## generating trend operator matrix "S：
    raw_x = x  # save the raw data before HP
    n = len(x)  # data size

    I_n = np.eye(n)
    D_temp = np.vstack((np.zeros([1, n]), np.eye(n - 1, n)))
    D_temp = np.dot((I_n - D_temp), (I_n - D_temp))
    D = D_temp[2:n].T
    S = np.linalg.inv(I_n + lam * np.dot(D, D.T))  # Equation 4 in PJ
    mS = I_n - S

    ##########################################################################

    ## the simple HP-filter
    if not iter:
        print("Original HP filter.")
        x_f = np.dot(S, x)
        x_c = x - x_f
        result = {"cycle": x_c, "trend_hist": x_f, \
                  "stopping": "nonstop", "trend": x - x_c, "raw_data": raw_x}

    ##########################################################################

    ## The Boosted HP-filter
    if iter:
        ### ADF test as the stopping criterion
        if stopping == "adf":

            print("Boosted HP-ADF.")

            r = 1
            stationary = False
            x_c = x

            x_f = np.zeros([n, Max_Iter])
            adf_p = np.zeros([Max_Iter, 1])

            while (r <= Max_Iter) and (not stationary):

                x_c = np.dot(mS, x_c)
                x_f[:, [r - 1]] = x - x_c
                adf_p_r = ts.adfuller(x_c, maxlag=math.floor(pow(n - 1, 1 / 3)), autolag=None, \
                                      regression="ct")[1]

                # x_c is the residual after the mean and linear trend being removed by HP filter
                # we use the critical value for the ADF distribution with
                # the intercept and linear trend specification

                adf_p[[r - 1]] = adf_p_r
                stationary = adf_p_r <= sig_p

                # Truncate the storage matrix and vectors
                if stationary:
                    R = r
                    x_f = x_f[:, 0:R]
                    adf_p = adf_p[0:R]
                    break

                r += 1

            if r > Max_Iter:
                R = Max_Iter
                logging.warning("The number of iterations exceeds Max_Iter. \
                The residual cycle remains non-stationary.")

            result = {"cycle": x_c, "trend_hist": x_f, "stopping": stopping,
                      "signif_p": sig_p, "adf_p_hist": adf_p, "iter_num": R,
                      "trend": x - x_c, "raw_data": raw_x}


        else:  # either BIC or nonstopping

            # assignment
            r = 0
            x_c_r = x
            x_f = np.zeros([n, Max_Iter])
            IC = np.zeros([Max_Iter, 1])
            # IC_decrease = True

            I_S_0 = I_n - S
            c_HP = np.dot(I_S_0, x)
            I_S_r = I_S_0

            while r < Max_Iter:

                r += 1

                x_c_r = np.dot(I_S_r, x)
                x_f[:, [r - 1]] = x - x_c_r
                B_r = I_n - I_S_r
                IC[[r - 1]] = np.var(x_c_r) / np.var(c_HP) + \
                              np.log(n) / (n - np.sum(np.diag(S))) * np.sum(np.diag(B_r))

                I_S_r = np.dot(I_S_0, I_S_r)  # update for the next round

                if r >= 2 and stopping == "BIC":
                    if IC[[r - 2]] < IC[[r - 1]]:
                        break

            # final assignment
            R = r - 1
            x_f = x_f[:, list(range(0, R))]
            x_c = x - x_f[:, [R - 1]]

            if stopping == "BIC":
                print("Boosted HP-BIC.")
                # save the path of BIC till iter+1 times to keep the "turning point" of BIC history.
                result = {"cycle": x_c, "trend_hist": x_f, "stopping": stopping,
                          "BIC_hist": IC[0:(R + 1)], "iter_num": R, "trend": x - x_c, "raw_data": raw_x}

            if stopping == "nonstop":
                print('Boosted HP-BIC with stopping = "nonstop".')
                result = {"cycle": x_c, "trend_hist": x_f, "stopping": stopping,
                          "BIC_hist": IC, "iter_num": Max_Iter - 1, "trend": x - x_c, "raw_data": raw_x}

    return result


def main():
    root = Tk()
    root.withdraw()
    messagebox.showinfo(
        "数据格式要求",
        "所提供的数据格式：\n请选择需要分析的代码。\n第一行为标题，第二行为列名，第三行开始为数据。\n数据必须以日期开始，即第一列必须为日期。"
    )

    # 让用户选择 Excel 文件
    in_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    if not in_path:
        print("未选择文件。")
        return

    # 读取用户选择的 Excel 文件
    df = pd.read_excel(in_path, header=1)  # 从第二行开始读取数据，即列名所在的行

    # 转换日期格式为 yyyy-mm-dd，如果无法解析则忽略
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce').dt.strftime('%Y-%m-%d')
    df.dropna(subset=[df.columns[0]], inplace=True)  # 删除日期列中的NaT值

    # 再次设置列名，因为转换日期格式后列名可能会丢失
    header_row = pd.read_excel(in_path, nrows=1).iloc[0]  # 读取第二行作为列名
    df.columns = header_row  # 将列名设置为第二行的值

    # 获取 lambda 值
    time_period = simpledialog.askstring(
        "Time Period", "请输入数据的时间频率：\n1代表日，2代表月，3代表年。", initialvalue="2"
    )
    lam_values = {"1": 129600, "2": 1600, "3": 6.25}
    lam = lam_values.get(time_period, 1600)

    # 对每一列数据（除日期外）进行 HP 滤波
    for col in df.columns[1:]:
        cycle, trend = hpfilter(df[col].dropna(), lamb=lam)
        df[col + '_trend'] = trend
        df[col + '_cycle'] = cycle

    # 准备输出路径
    out_path = os.path.splitext(in_path)[0] + "_HP_results.xlsx"

    # 将结果写入新的 Excel 文件，不包括索引
    with pd.ExcelWriter(out_path) as writer:
        df.to_excel(writer, index=False)

    print(f"结果保存成功，保存路径为：{out_path}")


if __name__ == "__main__":
    main()