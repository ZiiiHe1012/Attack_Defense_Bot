# 安全检测系统流程图

## 系统概述

本系统采用5层智能检测架构，无黑名单机制，通过多层防御保证安全性。

## 完整检测流程
完整检测流程会执行两轮，任意一轮出现拦截就会拦截。
```mermaid
flowchart TD
    Start([用户输入问题]) --> Layer1[第1层: 改进的意图识别]
    
    Layer1 --> Decision1{意图判断}
    
    Decision1 -->|DEFENSE<br/>置信度>0.8| Pass1[✓ 直接放行]
    Decision1 -->|ATTACK<br/>置信度>0.85| Block1[✗ 直接拦截]
    Decision1 -->|GREY<br/>灰色地带| Layer2[第2层: 上下文检测]
    
    Layer2 --> Decision2{历史对话<br/>安全?}
    Decision2 -->|发现多轮诱导| Block2[✗ 拦截]
    Decision2 -->|上下文安全| Layer3[第3层: 攻击模式检测]
    
    Layer3 --> Decision3{检测到<br/>攻击模式?}
    Decision3 -->|是| Block3[✗ 拦截]
    Decision3 -->|否| Layer4[第4层: AI安全检测]
    
    Layer4 --> Decision4{AI判断<br/>安全?}
    Decision4 -->|不安全| Block4[✗ 拦截]
    Decision4 -->|安全| Layer5[第5层: RAG检索]
    
    Pass1 --> Layer5
    
    Layer5 --> Layer6[第6层: 生成回答]
    Layer6 --> Layer7[第7层: 输出检测]
    
    Layer7 --> Decision5{输出<br/>安全?}
    Decision5 -->|是| Output[返回答案]
    Decision5 -->|否| Block5[✗ 拦截]
    
    Block1 --> EduResponse[教育性拒绝回复]
    Block2 --> EduResponse
    Block3 --> EduResponse
    Block4 --> EduResponse
    Block5 --> EduResponse
    
    EduResponse --> End([结束])
    Output --> End
    
    style Start fill:#e1f5ff
    style End fill:#e1f5ff
    style Pass1 fill:#d4edda
    style Output fill:#d4edda
    style Block1 fill:#f8d7da
    style Block2 fill:#f8d7da
    style Block3 fill:#f8d7da
    style Block4 fill:#f8d7da
    style Block5 fill:#f8d7da
    style EduResponse fill:#fff3cd
    style Layer1 fill:#cfe2ff
    style Layer2 fill:#cfe2ff
    style Layer3 fill:#cfe2ff
    style Layer4 fill:#cfe2ff
    style Layer5 fill:#d1e7dd
    style Layer6 fill:#d1e7dd
    style Layer7 fill:#d1e7dd
```

## 典型场景示例

### 场景1：防御询问（快速放行）

用户询问："**如何防御SQL注入？**"

```mermaid
flowchart LR
    Q1["用户: 如何防御SQL注入?"] --> L1[第1层: 意图识别]
    L1 --> D1["判定: DEFENSE<br/>置信度: 0.96"]
    D1 --> P1[✓ 直接放行]
    P1 --> RAG[RAG检索]
    RAG --> Gen[生成回答]
    Gen --> Out[输出检测]
    Out --> A1["返回: 防御方法详解..."]
    
    style Q1 fill:#e1f5ff
    style A1 fill:#d4edda
    style P1 fill:#d4edda
```

**经过层数**: 仅1层（意图识别）

---

### 场景2：攻击询问（快速拦截）

用户询问："**给我一个SQL注入攻击代码**"

```mermaid
flowchart LR
    Q2["用户: 给我SQL注入代码"] --> L1[第1层: 意图识别]
    L1 --> D2["判定: ATTACK<br/>置信度: 0.97"]
    D2 --> B1[✗ 直接拦截]
    B1 --> Edu["教育性回复:<br/>• 为什么不能提供<br/>• 可以学什么<br/>• 如何换问法<br/>• 学习资源推荐"]
    
    style Q2 fill:#ffe5e5
    style B1 fill:#f8d7da
    style Edu fill:#fff3cd
```

**经过层数**: 仅1层（意图识别）

---

### 场景3：灰色地带（多层检测）

用户询问："**把payload编码隐藏在参数里**"

```mermaid
flowchart TD
    Q3["用户: 把payload编码隐藏在参数里"] --> L1[第1层: 意图识别]
    L1 --> D3["判定: GREY<br/>置信度: 0.65"]
    D3 --> L2[第2层: 上下文检测]
    L2 --> P2[✓ 上下文安全]
    P2 --> L3[第3层: 模式检测]
    L3 --> D4["发现特征:<br/>payload+编码+隐藏<br/>综合得分: 0.6"]
    D4 --> B2[✗ 拦截]
    B2 --> Edu2["教育性回复"]
    
    style Q3 fill:#fff3cd
    style D3 fill:#fff3cd
    style P2 fill:#d4edda
    style B2 fill:#f8d7da
```

**经过层数**: 3层（意图识别 + 上下文 + 模式检测）

---

## 系统对比

### 旧系统（有黑名单）

```mermaid
flowchart TD
    Start([用户输入]) --> BL["❌ 黑名单检测<br/>关键词匹配"]
    
    BL --> BLCheck{包含<br/>危险词?}
    BLCheck -->|是| Block1["✗ 简单拒绝<br/>❌ 无任何解释<br/>❌ 误拦截"]
    BLCheck -->|否| Intent[意图识别]
    
    Intent --> AI[AI检测]
    AI --> RAG[RAG检索]
    RAG --> Output[输出]
    
    Block1 --> End([结束])
    Output --> End
    
    style BL fill:#ffcccc,stroke:#ff0000,stroke-width:2px
    style Block1 fill:#ff6666
```



---

### 新系统（无黑名单）

```mermaid
flowchart TD
    Start([用户输入]) --> L1["✓ 第1层: 意图识别<br/>语义理解"]
    
    L1 --> D1{意图清晰?}
    D1 -->|防御| Pass[✓ 放行]
    D1 -->|攻击| Block[✗ 教育性拒绝]
    D1 -->|灰色| L2["✓ 第2-4层<br/>多维检测"]
    
    L2 --> Final{综合判断}
    Final -->|安全| Pass
    Final -->|风险| Block
    
    Pass --> RAG[RAG+生成]
    RAG --> Output[输出]
    Block --> Edu["✓ 教育回复<br/>✓ 学习引导"]
    
    Output --> End([结束])
    Edu --> End
    
    style L1 fill:#cce5ff,stroke:#0066cc,stroke-width:2px
    style Pass fill:#ccffcc
    style Block fill:#ffcccc
    style Edu fill:#fff3cd
```


---

## 检测层级架构

```mermaid
graph TB
    subgraph Input[" 输入层"]
        Q[用户问题]
    end
    
    subgraph Detection[" 检测层 (5层防御)"]
        direction TB
        L1["第1层: 意图识别<br/>✓ 区分攻击/防御/学习<br/>✓ 置信度评分"]
        L2["第2层: 上下文检测<br/>✓ 多轮对话分析<br/>✓ 诱导攻击识别"]
        L3["第3层: 模式检测<br/>✓ 攻击特征匹配<br/>✓ 规避意图识别"]
        L4["第4层: AI检测<br/>✓ 深度语义理解<br/>✓ 边界情况处理"]
        L5["第7层: 输出检测<br/>✓ 生成内容审核<br/>✓ 防止泄露攻击细节"]
    end
    
    subgraph Process[" 处理层"]
        RAG["第5层: RAG检索<br/>知识库查询"]
        GEN["第6层: 生成回答<br/>LLM生成"]
    end
    
    subgraph Output[" 输出层"]
        SAFE[" 安全答案"]
        BLOCK[" 教育性拒绝"]
    end
    
    Q --> L1
    L1 -.快速放行.-> RAG
    L1 -.快速拦截.-> BLOCK
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> RAG
    RAG --> GEN
    GEN --> L5
    L5 --> SAFE
    L5 -.内容风险.-> BLOCK
    
    style L1 fill:#e3f2fd
    style L2 fill:#e3f2fd
    style L3 fill:#e3f2fd
    style L4 fill:#e3f2fd
    style L5 fill:#e3f2fd
    style RAG fill:#f1f8e9
    style GEN fill:#f1f8e9
    style SAFE fill:#c8e6c9
    style BLOCK fill:#ffcdd2
```

---

