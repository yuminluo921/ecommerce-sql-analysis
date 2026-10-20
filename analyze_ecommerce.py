import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# 核心修复：设置支持中文的字体（Mac 系统）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] # 指定默认字体为苹果自带的中文字体
plt.rcParams['axes.unicode_minus'] = False             # 解决保存图像是负号'-'显示为方块的问题
from sqlalchemy import create_engine

# 1. 连接数据库
db_password = os.getenv("MYSQL_PASSWORD")
engine = create_engine(f'mysql+pymysql://root:{db_password}@localhost:3306/sql_practice')

# 2. 查询数据（SQL保持不变）
sql = """
WITH first_order AS (
    SELECT c.customer_unique_id AS user_id, MIN(DATE(o.order_purchase_timestamp)) AS first_date
    FROM orders o JOIN customers c ON o.customer_id = c.customer_id
    WHERE DATE(o.order_purchase_timestamp) BETWEEN '2017-01-01' AND '2017-01-31'
    GROUP BY c.customer_unique_id
),
all_orders AS (
    SELECT c.customer_unique_id AS user_id, DATE(o.order_purchase_timestamp) AS order_date
    FROM orders o JOIN customers c ON o.customer_id = c.customer_id
    WHERE DATE(o.order_purchase_timestamp) >= '2017-01-01'
    GROUP BY c.customer_unique_id, DATE(o.order_purchase_timestamp)
)
SELECT f.first_date, COUNT(DISTINCT f.user_id) AS new_users,
       COUNT(DISTINCT CASE WHEN a.order_date > f.first_date THEN a.user_id END) AS repeat_users
FROM first_order f JOIN all_orders a ON f.user_id = a.user_id
GROUP BY f.first_date ORDER BY f.first_date;
"""
df = pd.read_sql(sql, engine)

# --- 关键修复：把字符串日期转换成 datetime 类型 ---
df['first_date'] = pd.to_datetime(df['first_date'])

# 3. 绘图（改用 Pandas 原生绘图，直接搞定双轴）
fig, ax1 = plt.subplots(figsize=(12, 6))

# 画柱状图（左轴）
df.plot(kind='bar', x='first_date', y='new_users', ax=ax1, color='skyblue', width=0.5, label='新增用户数')
ax1.set_ylabel('新增用户数', color='skyblue')
ax1.tick_params(axis='y', labelcolor='skyblue')
ax1.set_xlabel('首单日期')
ax1.set_xticklabels(df['first_date'].dt.strftime('%m-%d'), rotation=45) # 美化日期显示

# 画折线图（右轴）
ax2 = ax1.twinx()
df.plot(kind='line', x='first_date', y='repeat_users', ax=ax2, color='red', marker='o', label='累计复购用户数')
ax2.set_ylabel('累计复购用户数', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# 合并图例
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.title('Olist 每日新增用户数与累计复购用户数')
plt.tight_layout()
plt.savefig('ecommerce_retention.png', dpi=300)
plt.show()

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# Mac 中文字体设置
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 1. 连接数据库
db_password = os.getenv("MYSQL_PASSWORD")
engine = create_engine(f'mysql+pymysql://root:{db_password}@localhost:3306/sql_practice')


# 3. 用 SQL 拉取 RFM 原始数据
print("正在从数据库提取 RFM 数据...")
sql = """
WITH user_rfm_raw AS (
    SELECT 
        c.customer_unique_id AS user_id,
        DATEDIFF((SELECT MAX(DATE(order_purchase_timestamp)) FROM orders), MAX(DATE(o.order_purchase_timestamp))) AS recency,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(p.payment_value) AS monetary
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN payments p ON o.order_id = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT * FROM user_rfm_raw;
"""
df = pd.read_sql(sql, engine)
print(f"成功获取 {len(df)} 个用户的数据！")

# 4. 数据预处理
# 加上 1 是为了防止 log(0) 报错
df['recency_log'] = np.log1p(df['recency'])
df['frequency_log'] = np.log1p(df['frequency'])
df['monetary_log'] = np.log1p(df['monetary'])

# 提取特征列进行标准化
features = ['recency_log', 'frequency_log', 'monetary_log']
scaler = StandardScaler()
df_scaled = scaler.fit_transform(df[features])

# 5. K-Means 聚类 (分 4 类)
print("正在进行 K-Means 聚类...")
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(df_scaled)

# 看看这4类人的原始 RFM 平均数值
cluster_summary = df.groupby('cluster')[['recency', 'frequency', 'monetary']].mean()
print("\n各类用户的平均 R/F/M 值：\n", cluster_summary)


# 5. K-Means 聚类
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(df_scaled)

# 查看聚类中心，并根据上面终端输出的平均值，手动映射业务标签
# 注意：K-Means每次跑出来的 cluster 编号(0,1,2,3)可能会变，你要看终端输出的 R/F/M 平均值来对应！
cluster_labels = {
    0: '一般挽留客户',
    1: '重要保持客户',
    2: '重要发展客户',
    3: '重要价值客户'
}
df['segment'] = df['cluster'].map(cluster_labels)

# 6 画图：用 Seaborn 画 2D 散点图（X轴是R，Y轴是M，颜色代表分类）
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='recency', y='monetary', hue='segment', palette='Set1', alpha=0.6)
plt.title('Olist 用户分层：基于 Recency 与 Monetary 的聚类')
plt.xlabel('Recency (最近一次消费距今的天数)')
plt.ylabel('Monetary (累计消费金额)')
plt.legend(title='用户分层')
plt.tight_layout()
plt.savefig('rfm_clustering_2d.png', dpi=300)
plt.show()
