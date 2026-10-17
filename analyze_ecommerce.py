import os
import pandas as pd
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