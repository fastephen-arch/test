# Enhanced HSK/USDT Price Monitor

这是一个高级的HSK/USDT价格监控脚本，具备全面的技术分析功能，可实时监控HashKey代币的价格变动并发送通知。

## 功能特性

- **实时价格监控**: 每10分钟自动检查HSK/USDT交易对的最新价格
- **技术分析指标**:
  - 趋势分析 (看涨/看跌)
  - 简单移动平均线 (SMA)
  - 指数移动平均线 (EMA)
  - 相对强弱指数 (RSI)
  - 支撑位和阻力位分析
  - 波动率计算
  - 动量指标
- **K线分析**: 提供6小时周期内的K线趋势分析
- **飞书机器人集成**: 自动向飞书群组发送价格更新和技术分析报告

## 技术指标说明

- **SMA (Simple Moving Average)**: 简单移动平均线，用于识别价格趋势
- **EMA (Exponential Moving Average)**: 指数移动平均线，对近期价格变化更敏感
- **RSI (Relative Strength Index)**: 相对强弱指数，判断超买/超卖状态
- **支撑位/阻力位**: 识别价格的关键支撑和阻力水平
- **波动率**: 价格波动程度的衡量指标
- **动量**: 价格变动速度和强度的指标

## 使用场景

- 加密货币投资者需要实时监控HSK价格
- 交易员需要技术分析辅助决策
- 关注HashKey生态发展的社区成员

## 技术架构

- Python 3.x
- Requests库用于API调用
- Gate.io API获取实时价格数据
- 飞书Webhook机器人推送通知

## 部署方式

1. 克隆此仓库
2. 安装依赖: `pip install requests`
3. 配置飞书机器人Webhook URL
4. 运行脚本: `python enhanced_hsk_monitor.py`

## 注意事项

- 该脚本依赖Gate.io API获取价格数据
- 需要有效的飞书机器人Webhook URL以接收通知
- 请遵守API调用频率限制

## 作者

fastephen-arch