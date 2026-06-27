import AppKit
import WebKit

// MARK: - UI Helpers
private func glassCard() -> NSVisualEffectView {
    let v = NSVisualEffectView()
    v.wantsLayer = true
    v.material = .hudWindow
    v.blendingMode = .withinWindow
    v.state = .active
    v.layer?.cornerRadius = 16
    v.layer?.borderWidth = 1
    v.layer?.borderColor = Theme.shared.border.cgColor
    v.layer?.backgroundColor = Theme.shared.cardBg.cgColor
    return v
}

private func mkLabel(_ text: String, size: CGFloat, weight: NSFont.Weight) -> NSTextField {
    let l = NSTextField(labelWithString: text)
    l.font = NSFont.systemFont(ofSize: size, weight: weight)
    l.translatesAutoresizingMaskIntoConstraints = false
    return l
}

private func mkPillBtn(_ title: String) -> NSButton {
    let b = NSButton(title: title, target: nil, action: nil)
    b.bezelStyle = .rounded
    b.isBordered = false
    b.wantsLayer = true
    b.layer?.backgroundColor = Theme.shared.cardBg.cgColor
    b.layer?.cornerRadius = 13
    b.layer?.borderWidth = 1
    b.layer?.borderColor = Theme.shared.border.cgColor
    b.font = NSFont.systemFont(ofSize: 11, weight: .medium)
    b.contentTintColor = Theme.shared.textPrimary
    b.translatesAutoresizingMaskIntoConstraints = false
    return b
}

private func mkPrimaryBtn(_ title: String) -> NSButton {
    let b = NSButton(title: title, target: nil, action: nil)
    b.bezelStyle = .rounded
    b.wantsLayer = true
    b.layer?.backgroundColor = Theme.shared.accent.cgColor
    b.layer?.cornerRadius = 7
    b.contentTintColor = .white
    b.font = NSFont.systemFont(ofSize: 12, weight: .semibold)
    b.translatesAutoresizingMaskIntoConstraints = false
    return b
}

private func mkSuccessBtn(_ title: String) -> NSButton {
    let b = NSButton(title: title, target: nil, action: nil)
    b.bezelStyle = .rounded
    b.wantsLayer = true
    b.layer?.backgroundColor = Theme.shared.success.cgColor
    b.layer?.cornerRadius = 7
    b.contentTintColor = .white
    b.font = NSFont.systemFont(ofSize: 12, weight: .semibold)
    b.translatesAutoresizingMaskIntoConstraints = false
    return b
}

private func mkOutlineBtn(_ title: String) -> NSButton {
    let b = NSButton(title: title, target: nil, action: nil)
    b.bezelStyle = .rounded
    b.isBordered = true
    b.wantsLayer = true
    b.layer?.cornerRadius = 7
    b.layer?.borderWidth = 1
    b.layer?.borderColor = Theme.shared.border.cgColor
    b.font = NSFont.systemFont(ofSize: 12, weight: .medium)
    b.translatesAutoresizingMaskIntoConstraints = false
    return b
}

// MARK: - Theme
class Theme {
    static let shared = Theme()
    var isDark = false

    var bg: NSColor {
        isDark ? NSColor(white: 0.10, alpha: 1) : NSColor(white: 0.95, alpha: 1)
    }
    var cardBg: NSColor {
        isDark ? NSColor(white: 0.16, alpha: 0.88) : NSColor.white.withAlphaComponent(0.72)
    }
    var textPrimary: NSColor {
        isDark ? .white : NSColor(white: 0.12, alpha: 1)
    }
    var textSecondary: NSColor {
        isDark ? NSColor.white.withAlphaComponent(0.48) : NSColor(white: 0.42, alpha: 1)
    }
    var accent: NSColor { NSColor(red: 0.40, green: 0.49, blue: 0.92, alpha: 1) }
    var success: NSColor { NSColor(red: 0.29, green: 0.85, blue: 0.50, alpha: 1) }
    var danger: NSColor { NSColor(red: 0.95, green: 0.42, blue: 0.40, alpha: 1) }
    var warning: NSColor { NSColor(red: 1.0, green: 0.76, blue: 0.03, alpha: 1) }
    var border: NSColor {
        isDark ? NSColor.white.withAlphaComponent(0.09) : NSColor.white.withAlphaComponent(0.5)
    }

    func applyDark(_ dark: Bool) {
        isDark = dark
        NSApp.appearance = dark ? NSAppearance(named: .darkAqua) : NSAppearance(named: .aqua)
    }
}

// MARK: - L10n
struct L10n {
    static var d: [String: String] = [
        "title":"Agent Mesh Console","subtitle":"统一Agent通信平台",
        "connecting":"连接中...","connected":"已连接","disconnected":"未连接",
        "online":"在线","registered":"已注册","pending":"待确认","queue":"消息队列","tasks":"任务",
        "confirm_all":"确认全部","start_all":"启动全部","refresh":"刷新",
        "dark_mode":"深色","light_mode":"浅色","agents":"Agent列表",
        "pending_agents":"待确认","recent":"最近活动","no_agents":"暂无Agent",
        "no_pending":"暂无待确认","no_activity":"暂无活动",
        "confirm":"确认","reject":"拒绝","clear":"清除",
        "zh":"中文","en":"EN","loading":"加载中...",
        "start_agent":"启动Agent","ping_agent":"Ping检测",
        "chat_with":"与 Agent 聊天","send":"发送","type_placeholder":"输入消息...",
        "last_seen":"最后在线","capabilities":"能力","connection":"连接信息",
        "online_":"在线","offline_":"离线","start":"启动","stop":"停止",
        "chat":"聊天","details":"详情","no_chat":"选择 Agent 开始聊天",
        "sent":"发送","received":"收到","ping_success":"Ping 成功","ping_failed":"Ping 失败 - Agent离线",
        "message_sent":"消息已发送","message_failed":"发送失败",
        "confirm_success":"已确认","confirm_failed":"确认失败",
        "start_success":"已启动","start_failed":"启动失败",
    ]

    static func t(_ k: String) -> String { d[k] ?? k }
    static var zh = true

    static func setLang(_ z: Bool) {
        zh = z
        d = z ? zhDict : enDict
        NotificationCenter.default.post(name: .langChanged, object: nil)
    }

    static let zhDict = L10n.d
    static let enDict: [String: String] = [
        "title":"Agent Mesh Console","subtitle":"Unified Agent Communication Platform",
        "connecting":"Connecting...","connected":"Connected","disconnected":"Disconnected",
        "online":"Online","registered":"Registered","pending":"Pending","queue":"Queue","tasks":"Tasks",
        "confirm_all":"Confirm All","start_all":"Start All","refresh":"Refresh",
        "dark_mode":"Dark","light_mode":"Light","agents":"Agent List",
        "pending_agents":"Pending","recent":"Recent Activity","no_agents":"No Agents",
        "no_pending":"No Pending","no_activity":"No Activity",
        "confirm":"Confirm","reject":"Reject","clear":"Clear",
        "zh":"中文","en":"EN","loading":"Loading...",
        "start_agent":"Start Agent","ping_agent":"Ping",
        "chat_with":"Chat with Agent","send":"Send","type_placeholder":"Type a message...",
        "last_seen":"Last Seen","capabilities":"Capabilities","connection":"Connection",
        "online_":"Online","offline_":"Offline","start":"Start","stop":"Stop",
        "chat":"Chat","details":"Details","no_chat":"Select an Agent to chat",
        "sent":"Sent","received":"Received","ping_success":"Ping OK","ping_failed":"Ping Failed - Agent Offline",
        "message_sent":"Message sent","message_failed":"Failed to send",
        "confirm_success":"Confirmed","confirm_failed":"Failed",
        "start_success":"Started","start_failed":"Failed to start",
    ]
}
extension Notification.Name { static let langChanged = Notification.Name("langChanged") }

// MARK: - Models
struct Agent: Codable, Identifiable {
    let id: String
    let name: String
    let type: String
    let status: String
    let capabilities: [String]?
    let lastSeen: String?
    let createdAt: String?
    enum Keys: String, CodingKey {
        case id, name, type, status, capabilities
        case lastSeen = "last_seen"; case createdAt = "created_at"
    }
}

struct AgentDetail: Codable {
    let status: String
    let agent: Agent
    let isOnline: Bool
    let connectionInfo: ConnectionInfo?
    let offlineReason: String?
    enum Keys: String, CodingKey {
        case status, agent, isOnline = "is_online"
        case connectionInfo = "connection_info"
        case offlineReason = "offline_reason"
    }
}

struct ConnectionInfo: Codable {
    let agentId: String?
    let connectedAt: String?
    let durationSeconds: Double?
    enum Keys: String, CodingKey {
        case agentId = "agent_id"; case connectedAt = "connected_at"
        case durationSeconds = "duration_seconds"
    }
}

struct ChatMessage: Codable, Identifiable {
    let id: String
    let type: String
    let from: String
    let to: String
    let payload: [String: AnyCodable]?
    let timestamp: String?
    var text: String { payload?["text"]?.stringValue ?? "" }
    enum Keys: String, CodingKey { case id, type, from, to, payload, timestamp }
}

struct AnyCodable: Codable {
    let stringValue: String?
    let intValue: Int?
    let doubleValue: Double?
    let boolValue: Bool?

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        stringValue = try? container.decode(String.self)
        intValue = try? container.decode(Int.self)
        doubleValue = try? container.decode(Double.self)
        boolValue = try? container.decode(Bool.self)
    }
    init(string: String) { stringValue = string; intValue = nil; doubleValue = nil; boolValue = nil }
    func encode(to encoder: Encoder) throws { var c = encoder.singleValueContainer(); try? c.encode(stringValue); try? c.encode(intValue); try? c.encode(doubleValue); try? c.encode(boolValue) }
}

struct Stats: Codable {
    let agents: AgentStats?
    let onlineCount: Int?
    let queueSize: Int?
    let taskCount: Int?
    enum Keys: String, CodingKey {
        case agents; case onlineCount = "online_count"
        case queueSize = "queue_size"; case taskCount = "task_count"
    }
}
struct AgentStats: Codable {
    let confirmedCount: Int?; let pendingCount: Int?
    enum Keys: String, CodingKey { case confirmedCount = "confirmed_count"; case pendingCount = "pending_count" }
}

// MARK: - ConsoleViewController
class ConsoleViewController: NSViewController {

    // MARK: Properties
    private var splitView: NSSplitView!
    private var leftPanel: NSView!           // Agent list + stats
    private var rightPanel: NSView!          // Detail + Chat
    private var agentList: NSTableView!
    private var pendingList: NSTableView!
    private var statsCards: [String: StatCard] = [:]

    // Right panel
    private var detailView: AgentDetailView!
    private var chatView: ChatPanelView!

    // Toolbar
    private var statusDot: NSView!
    private var statusLabel: NSTextField!
    private var langBtn: NSButton!
    private var darkBtn: NSButton!

    // Action buttons
    private var confirmAllBtn: NSButton!
    private var startAllBtn: NSButton!
    private var refreshBtn: NSButton!

    // Header labels
    private var titleLabel: NSTextField!
    private var subtitleLabel: NSTextField!
    private var agentHeaderLabel: NSTextField!
    private var pendingHeaderLabel: NSTextField!

    // State
    private var agents: [Agent] = []
    private var pendingAgents: [Agent] = []
    private var selectedAgent: Agent?
    private var selectedAgentDetail: AgentDetail?
    private var refreshTimer: Timer?
    private var langObs: NSObjectProtocol?
    private var wsTask: URLSessionWebSocketTask?
    private var wsConnected = false

    private let server = "http://127.0.0.1:18801"
    private let wsServer = "ws://127.0.0.1:18800"
    private let consoleId = "mesh-console-\(UUID().uuidString.prefix(8))"

    // MARK: Lifecycle
    override func loadView() {
        view = NSView(frame: NSRect(x: 0, y: 0, width: 1280, height: 820))
        view.wantsLayer = true
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        connectWebSocket()
        loadData()
        startPolling()
        langObs = NotificationCenter.default.addObserver(forName: .langChanged, object: nil, queue: .main) { [weak self] _ in
            self?.refreshLabels()
        }
    }

    deinit { if let o = langObs { NotificationCenter.default.removeObserver(o) } }

    // MARK: Setup
    private func setupUI() {
        // Background
        let bgView = NSVisualEffectView(frame: view.bounds)
        bgView.autoresizingMask = [.width,.height]
        bgView.material = .hudWindow
        bgView.blendingMode = .behindWindow
        bgView.state = .active
        bgView.layer?.cornerRadius = 0
        view.addSubview(bgView)

        // Top toolbar
        let toolbar = glassCard()
        toolbar.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(toolbar)

        titleLabel = mkLabel(L10n.t("title"), size: 20, weight: .bold)
        titleLabel.textColor = Theme.shared.textPrimary
        toolbar.addSubview(titleLabel)

        subtitleLabel = mkLabel(L10n.t("subtitle"), size: 11, weight: .regular)
        subtitleLabel.textColor = Theme.shared.textSecondary
        toolbar.addSubview(subtitleLabel)

        // Status pill
        let statusPill = NSView()
        statusPill.wantsLayer = true
        statusPill.layer?.backgroundColor = Theme.shared.cardBg.cgColor
        statusPill.layer?.cornerRadius = 14
        statusPill.layer?.borderWidth = 1
        statusPill.layer?.borderColor = Theme.shared.border.cgColor
        statusPill.translatesAutoresizingMaskIntoConstraints = false
        toolbar.addSubview(statusPill)

        statusDot = NSView()
        statusDot.wantsLayer = true
        statusDot.layer?.cornerRadius = 5
        statusDot.layer?.backgroundColor = NSColor.gray.cgColor
        statusDot.translatesAutoresizingMaskIntoConstraints = false
        statusPill.addSubview(statusDot)

        statusLabel = mkLabel(L10n.t("connecting"), size: 11, weight: .medium)
        statusLabel.textColor = Theme.shared.textPrimary
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        statusPill.addSubview(statusLabel)

        langBtn = mkPillBtn(L10n.t("en"))
        langBtn.target = self
        langBtn.action = #selector(toggleLang)
        toolbar.addSubview(langBtn)

        darkBtn = mkPillBtn(L10n.t("dark_mode"))
        darkBtn.target = self
        darkBtn.action = #selector(toggleDark)
        toolbar.addSubview(darkBtn)

        // Stats bar
        let statsBar = NSStackView()
        statsBar.orientation = .horizontal
        statsBar.distribution = .fillEqually
        statsBar.spacing = 10
        statsBar.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(statsBar)

        for (id, icon) in [("online","●"),("total","◎"),("pending","◐"),("queue","☰"),("tasks","◇")] {
            let card = StatCard(id: id, icon: icon)
            statsCards[id] = card
            statsBar.addArrangedSubview(card)
        }

        // Action bar
        let actionBar = glassCard()
        actionBar.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(actionBar)

        confirmAllBtn = mkPrimaryBtn(L10n.t("confirm_all"))
        confirmAllBtn.target = self
        confirmAllBtn.action = #selector(confirmAll)
        actionBar.addSubview(confirmAllBtn)

        startAllBtn = mkSuccessBtn(L10n.t("start_all"))
        startAllBtn.target = self
        startAllBtn.action = #selector(startAll)
        actionBar.addSubview(startAllBtn)

        refreshBtn = mkOutlineBtn(L10n.t("refresh"))
        refreshBtn.target = self
        refreshBtn.action = #selector(doRefresh)
        actionBar.addSubview(refreshBtn)

        // Split view
        splitView = NSSplitView()
        splitView.isVertical = true
        splitView.dividerStyle = .thin
        splitView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(splitView)

        // Left panel
        leftPanel = NSView()
        leftPanel.wantsLayer = true

        let leftTop = glassCard()
        leftTop.translatesAutoresizingMaskIntoConstraints = false
        leftTop.wantsLayer = true
        leftTop.layer?.cornerRadius = 12
        leftPanel.addSubview(leftTop)

        agentHeaderLabel = mkLabel(L10n.t("agents"), size: 12, weight: .semibold)
        agentHeaderLabel.textColor = Theme.shared.textSecondary
        leftTop.addSubview(agentHeaderLabel)

        agentList = NSTableView()
        agentList.backgroundColor = .clear
        agentList.headerView = nil
        agentList.rowHeight = 52
        agentList.intercellSpacing = NSSize(width: 0, height: 3)
        agentList.selectionHighlightStyle = .regular
        agentList.dataSource = self
        agentList.delegate = self
        let agentCol = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("a"))
        agentCol.resizingMask = .autoresizingMask
        agentList.addTableColumn(agentCol)

        let agentScroll = NSScrollView()
        agentScroll.documentView = agentList
        agentScroll.hasVerticalScroller = true
        agentScroll.drawsBackground = false
        agentScroll.translatesAutoresizingMaskIntoConstraints = false
        leftTop.addSubview(agentScroll)

        let leftBottom = glassCard()
        leftBottom.translatesAutoresizingMaskIntoConstraints = false
        leftBottom.wantsLayer = true
        leftBottom.layer?.cornerRadius = 12
        leftPanel.addSubview(leftBottom)

        pendingHeaderLabel = mkLabel(L10n.t("pending_agents"), size: 12, weight: .semibold)
        pendingHeaderLabel.textColor = Theme.shared.textSecondary
        leftBottom.addSubview(pendingHeaderLabel)

        pendingList = NSTableView()
        pendingList.backgroundColor = .clear
        pendingList.headerView = nil
        pendingList.rowHeight = 52
        pendingList.intercellSpacing = NSSize(width: 0, height: 3)
        pendingList.selectionHighlightStyle = .regular
        pendingList.dataSource = self
        pendingList.delegate = self
        let pendCol = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("p"))
        pendCol.resizingMask = .autoresizingMask
        pendingList.addTableColumn(pendCol)

        let pendScroll = NSScrollView()
        pendScroll.documentView = pendingList
        pendScroll.hasVerticalScroller = true
        pendScroll.drawsBackground = false
        pendScroll.translatesAutoresizingMaskIntoConstraints = false
        leftBottom.addSubview(pendScroll)

        // Right panel
        rightPanel = NSView()

        let detailCard = glassCard()
        detailCard.translatesAutoresizingMaskIntoConstraints = false
        detailCard.wantsLayer = true
        detailCard.layer?.cornerRadius = 12
        rightPanel.addSubview(detailCard)

        detailView = AgentDetailView()
        detailView.translatesAutoresizingMaskIntoConstraints = false
        detailView.onPing = { [weak self] in self?.pingAgent() }
        detailView.onStart = { [weak self] in self?.startSelectedAgent() }
        detailCard.addSubview(detailView)

        let chatCard = glassCard()
        chatCard.translatesAutoresizingMaskIntoConstraints = false
        chatCard.wantsLayer = true
        chatCard.layer?.cornerRadius = 12
        rightPanel.addSubview(chatCard)

        chatView = ChatPanelView()
        chatView.translatesAutoresizingMaskIntoConstraints = false
        chatView.onSend = { [weak self] text in self?.sendChatMessage(text) }
        chatCard.addSubview(chatView)

        // Add to split
        splitView.addArrangedSubview(leftPanel)
        splitView.addArrangedSubview(rightPanel)
        splitView.setHoldingPriority(.defaultLow, forSubviewAt: 0)
        splitView.setHoldingPriority(.defaultHigh, forSubviewAt: 1)

        // Layout
        NSLayoutConstraint.activate([
            toolbar.topAnchor.constraint(equalTo: view.topAnchor),
            toolbar.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            toolbar.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            toolbar.heightAnchor.constraint(equalToConstant: 64),

            titleLabel.leadingAnchor.constraint(equalTo: toolbar.leadingAnchor, constant: 18),
            titleLabel.topAnchor.constraint(equalTo: toolbar.topAnchor, constant: 12),

            subtitleLabel.leadingAnchor.constraint(equalTo: toolbar.leadingAnchor, constant: 18),
            subtitleLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 1),

            statusPill.trailingAnchor.constraint(equalTo: toolbar.trailingAnchor, constant: -16),
            statusPill.centerYAnchor.constraint(equalTo: toolbar.centerYAnchor),
            statusPill.heightAnchor.constraint(equalToConstant: 26),

            statusDot.leadingAnchor.constraint(equalTo: statusPill.leadingAnchor, constant: 9),
            statusDot.centerYAnchor.constraint(equalTo: statusPill.centerYAnchor),
            statusDot.widthAnchor.constraint(equalToConstant: 10),
            statusDot.heightAnchor.constraint(equalToConstant: 10),

            statusLabel.leadingAnchor.constraint(equalTo: statusDot.trailingAnchor, constant: 5),
            statusLabel.trailingAnchor.constraint(equalTo: statusPill.trailingAnchor, constant: -10),
            statusLabel.centerYAnchor.constraint(equalTo: statusPill.centerYAnchor),

            langBtn.trailingAnchor.constraint(equalTo: statusPill.leadingAnchor, constant: -10),
            langBtn.centerYAnchor.constraint(equalTo: toolbar.centerYAnchor),
            langBtn.widthAnchor.constraint(equalToConstant: 44),
            langBtn.heightAnchor.constraint(equalToConstant: 26),

            darkBtn.trailingAnchor.constraint(equalTo: langBtn.leadingAnchor, constant: -8),
            darkBtn.centerYAnchor.constraint(equalTo: toolbar.centerYAnchor),
            darkBtn.widthAnchor.constraint(equalToConstant: 60),
            darkBtn.heightAnchor.constraint(equalToConstant: 26),

            statsBar.topAnchor.constraint(equalTo: toolbar.bottomAnchor, constant: 10),
            statsBar.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 14),
            statsBar.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -14),
            statsBar.heightAnchor.constraint(equalToConstant: 80),

            actionBar.topAnchor.constraint(equalTo: statsBar.bottomAnchor, constant: 10),
            actionBar.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 14),
            actionBar.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -14),
            actionBar.heightAnchor.constraint(equalToConstant: 48),

            confirmAllBtn.leadingAnchor.constraint(equalTo: actionBar.leadingAnchor, constant: 14),
            confirmAllBtn.centerYAnchor.constraint(equalTo: actionBar.centerYAnchor),

            startAllBtn.leadingAnchor.constraint(equalTo: confirmAllBtn.trailingAnchor, constant: 10),
            startAllBtn.centerYAnchor.constraint(equalTo: actionBar.centerYAnchor),

            refreshBtn.trailingAnchor.constraint(equalTo: actionBar.trailingAnchor, constant: -14),
            refreshBtn.centerYAnchor.constraint(equalTo: actionBar.centerYAnchor),

            splitView.topAnchor.constraint(equalTo: actionBar.bottomAnchor, constant: 10),
            splitView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 14),
            splitView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -14),
            splitView.bottomAnchor.constraint(equalTo: view.bottomAnchor, constant: -14),

            // Left panel internal
            leftTop.topAnchor.constraint(equalTo: leftPanel.topAnchor),
            leftTop.leadingAnchor.constraint(equalTo: leftPanel.leadingAnchor),
            leftTop.trailingAnchor.constraint(equalTo: leftPanel.trailingAnchor),
            leftTop.bottomAnchor.constraint(equalTo: leftPanel.centerYAnchor, constant: -6),

            agentHeaderLabel.topAnchor.constraint(equalTo: leftTop.topAnchor, constant: 10),
            agentHeaderLabel.leadingAnchor.constraint(equalTo: leftTop.leadingAnchor, constant: 14),

            agentScroll.topAnchor.constraint(equalTo: agentHeaderLabel.bottomAnchor, constant: 8),
            agentScroll.leadingAnchor.constraint(equalTo: leftTop.leadingAnchor, constant: 6),
            agentScroll.trailingAnchor.constraint(equalTo: leftTop.trailingAnchor, constant: -6),
            agentScroll.bottomAnchor.constraint(equalTo: leftTop.bottomAnchor, constant: -8),

            leftBottom.topAnchor.constraint(equalTo: leftPanel.centerYAnchor, constant: 6),
            leftBottom.leadingAnchor.constraint(equalTo: leftPanel.leadingAnchor),
            leftBottom.trailingAnchor.constraint(equalTo: leftPanel.trailingAnchor),
            leftBottom.bottomAnchor.constraint(equalTo: leftPanel.bottomAnchor),

            pendingHeaderLabel.topAnchor.constraint(equalTo: leftBottom.topAnchor, constant: 10),
            pendingHeaderLabel.leadingAnchor.constraint(equalTo: leftBottom.leadingAnchor, constant: 14),

            pendScroll.topAnchor.constraint(equalTo: pendingHeaderLabel.bottomAnchor, constant: 8),
            pendScroll.leadingAnchor.constraint(equalTo: leftBottom.leadingAnchor, constant: 6),
            pendScroll.trailingAnchor.constraint(equalTo: leftBottom.trailingAnchor, constant: -6),
            pendScroll.bottomAnchor.constraint(equalTo: leftBottom.bottomAnchor, constant: -8),

            // Right panel internal
            detailCard.topAnchor.constraint(equalTo: rightPanel.topAnchor),
            detailCard.leadingAnchor.constraint(equalTo: rightPanel.leadingAnchor),
            detailCard.trailingAnchor.constraint(equalTo: rightPanel.trailingAnchor),
            detailCard.heightAnchor.constraint(equalToConstant: 180),

            detailView.topAnchor.constraint(equalTo: detailCard.topAnchor),
            detailView.leadingAnchor.constraint(equalTo: detailCard.leadingAnchor),
            detailView.trailingAnchor.constraint(equalTo: detailCard.trailingAnchor),
            detailView.bottomAnchor.constraint(equalTo: detailCard.bottomAnchor),

            chatCard.topAnchor.constraint(equalTo: detailCard.bottomAnchor, constant: 10),
            chatCard.leadingAnchor.constraint(equalTo: rightPanel.leadingAnchor),
            chatCard.trailingAnchor.constraint(equalTo: rightPanel.trailingAnchor),
            chatCard.bottomAnchor.constraint(equalTo: rightPanel.bottomAnchor),
        ])

        // Set split proportions
        splitView.setPosition(360, ofDividerAt: 0)
    }

    // MARK: - Refresh Labels
    private func refreshLabels() {
        titleLabel.stringValue = L10n.t("title")
        subtitleLabel.stringValue = L10n.t("subtitle")
        statusLabel.stringValue = wsConnected ? L10n.t("connected") : L10n.t("disconnected")
        langBtn.title = L10n.t("en")
        darkBtn.title = Theme.shared.isDark ? L10n.t("light_mode") : L10n.t("dark_mode")
        confirmAllBtn.title = L10n.t("confirm_all")
        startAllBtn.title = L10n.t("start_all")
        refreshBtn.title = L10n.t("refresh")
        agentHeaderLabel.stringValue = L10n.t("agents")
        pendingHeaderLabel.stringValue = L10n.t("pending_agents")

        statsCards.values.forEach { $0.refreshLabel(L10n.t($0.key)) }
        agentList.reloadData()
        pendingList.reloadData()
        detailView.refreshLabels()
        chatView.refreshLabels()
    }

    // MARK: - Theme
    private func updateTheme() {
        Theme.shared.applyDark(Theme.shared.isDark)

        for subview in view.subviews {
            if let card = subview as? NSVisualEffectView, card.layer?.cornerRadius == 16 || card.layer?.cornerRadius == 12 || card.layer?.cornerRadius == 0 {
                card.layer?.borderColor = Theme.shared.border.cgColor
                card.layer?.backgroundColor = Theme.shared.cardBg.cgColor
            }
        }

        titleLabel.textColor = Theme.shared.textPrimary
        subtitleLabel.textColor = Theme.shared.textSecondary
        statusLabel.textColor = Theme.shared.textPrimary
        langBtn.contentTintColor = Theme.shared.textPrimary
        darkBtn.layer?.backgroundColor = Theme.shared.cardBg.cgColor
        darkBtn.layer?.borderColor = Theme.shared.border.cgColor
        langBtn.layer?.backgroundColor = Theme.shared.cardBg.cgColor
        langBtn.layer?.borderColor = Theme.shared.border.cgColor

        agentHeaderLabel.textColor = Theme.shared.textSecondary
        pendingHeaderLabel.textColor = Theme.shared.textSecondary

        statsCards.values.forEach { $0.applyTheme() }
        agentList.reloadData()
        pendingList.reloadData()
        detailView.applyTheme()
        chatView.applyTheme()
    }

    // MARK: - Actions
    @objc private func toggleLang() { L10n.setLang(!L10n.zh) }
    @objc private func toggleDark() { Theme.shared.isDark.toggle(); updateTheme() }

    @objc func doRefresh() {
        loadData()
    }

    @objc private func confirmAll() {
        post("\(server)/api/agents/confirm-all", method: "POST") { [weak self] data, resp in
            let count = (data.flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String:Any] }?["count"] as? Int) ?? 0
            DispatchQueue.main.async {
                self?.chatView.addSystemMsg("已确认 \(count) 个Agent")
                self?.loadData()
            }
        }
    }

    @objc private func startAll() {
        post("\(server)/api/agents/start-all", method: "POST") { [weak self] data, resp in
            let count = (data.flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String:Any] }?["count"] as? Int) ?? 0
            DispatchQueue.main.async {
                self?.chatView.addSystemMsg("已启动 \(count) 个Agent")
                self?.loadData()
            }
        }
    }

    private func pingAgent() {
        guard let agent = selectedAgent else { return }
        get("\(server)/api/agents/\(agent.id.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed)!)/ping", method: "POST") { [weak self] data, _ in
            guard let d = data, let json = try? JSONSerialization.jsonObject(with: d) as? [String:Any] else { return }
            let online = json["online"] as? Bool ?? false
            DispatchQueue.main.async {
                if online {
                    self?.chatView.addSystemMsg("\(L10n.t("ping_success")): \(agent.name)")
                } else {
                    self?.chatView.addSystemMsg("\(L10n.t("ping_failed")): \(agent.name)")
                }
                self?.loadAgentDetail(agent.id)
            }
        }
    }

    private func startSelectedAgent() {
        guard let agent = selectedAgent else { return }
        post("\(server)/api/agents/\(agent.id.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed)!)/ping", method: "POST") { [weak self] _, _ in
            DispatchQueue.main.async {
                self?.chatView.addSystemMsg("\(L10n.t("start_success")): \(agent.name)")
                self?.loadData()
            }
        }
    }

    private func sendChatMessage(_ text: String) {
        guard let agent = selectedAgent, !text.isEmpty else { return }
        let body: [String:Any] = ["from": consoleId, "to": agent.id, "text": text]
        post("\(server)/api/messages/send", method: "POST", body: body) { [weak self] data, resp in
            DispatchQueue.main.async {
                if let http = resp as? HTTPURLResponse, http.statusCode == 200 {
                    self?.chatView.addSentMsg(text)
                    self?.loadChatHistory(agent.id)
                } else {
                    self?.chatView.addSystemMsg(L10n.t("message_failed"))
                }
            }
        }
    }

    // MARK: - Data Loading
    private func loadData() {
        loadStats()
        loadAgents()
        loadPendingAgents()
    }

    private func startPolling() {
        checkServer()
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            self?.checkServer()
            self?.loadData()
        }
    }

    private func checkServer() {
        guard let url = URL(string: "http://127.0.0.1:18800") else { return }
        var req = URLRequest(url: url)
        req.timeoutInterval = 2.0
        URLSession.shared.dataTask(with: req) { [weak self] _, resp, _ in
            let ok = (resp as? HTTPURLResponse) != nil
            DispatchQueue.main.async {
                self?.wsConnected = ok
                self?.statusDot.layer?.backgroundColor = ok ? Theme.shared.success.cgColor : Theme.shared.danger.cgColor
                self?.statusLabel.stringValue = ok ? L10n.t("connected") : L10n.t("disconnected")
            }
        }.resume()
    }

    private func loadStats() {
        get("\(server)/api/stats") { [weak self] data, _ in
            guard let d = data, let json = try? JSONSerialization.jsonObject(with: d) as? [String:Any] else { return }
            DispatchQueue.main.async {
                self?.statsCards["online"]?.setVal(json["online_count"] as? Int ?? 0)
                self?.statsCards["total"]?.setVal((json["agents"] as? [String:Any])?["confirmed_count"] as? Int ?? 0)
                self?.statsCards["pending"]?.setVal((json["agents"] as? [String:Any])?["pending_count"] as? Int ?? 0)
                self?.statsCards["queue"]?.setVal(json["queue_size"] as? Int ?? 0)
                self?.statsCards["tasks"]?.setVal(json["task_count"] as? Int ?? 0)
            }
        }
    }

    private func loadAgents() {
        get("\(server)/api/agents") { [weak self] data, _ in
            guard let d = data,
                  let json = try? JSONSerialization.jsonObject(with: d) as? [String:Any],
                  let list = json["agents"] as? [[String:Any]] else { return }
            let decoded = list.compactMap { dict -> Agent? in
                guard let jd = try? JSONSerialization.data(withJSONObject: dict, options: .fragmentsAllowed),
                      let a = try? JSONDecoder().decode(Agent.self, from: jd) else { return nil }
                return a
            }
            DispatchQueue.main.async {
                self?.agents = decoded
                self?.agentList.reloadData()
            }
        }
    }

    private func loadPendingAgents() {
        get("\(server)/api/agents/pending") { [weak self] data, _ in
            guard let d = data,
                  let json = try? JSONSerialization.jsonObject(with: d) as? [String:Any],
                  let list = json["agents"] as? [[String:Any]] else { return }
            let decoded = list.compactMap { dict -> Agent? in
                guard let jd = try? JSONSerialization.data(withJSONObject: dict, options: .fragmentsAllowed),
                      let a = try? JSONDecoder().decode(Agent.self, from: jd) else { return nil }
                return a
            }
            DispatchQueue.main.async {
                self?.pendingAgents = decoded
                self?.pendingList.reloadData()
            }
        }
    }

    private func loadAgentDetail(_ agentId: String) {
        let enc = agentId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? agentId
        get("\(server)/api/agents/\(enc)/detail") { [weak self] data, _ in
            guard let d = data,
                  let json = try? JSONSerialization.jsonObject(with: d) as? [String:Any],
                  let jd = try? JSONSerialization.data(withJSONObject: json["agent"] as Any, options: .fragmentsAllowed),
                  let agent = try? JSONDecoder().decode(Agent.self, from: jd) else { return }
            let isOnline = json["is_online"] as? Bool ?? false
            let reason = json["offline_reason"] as? String
            DispatchQueue.main.async {
                self?.selectedAgent = agent
                self?.selectedAgentDetail = AgentDetail(
                    status: agent.status,
                    agent: agent,
                    isOnline: isOnline,
                    connectionInfo: nil,
                    offlineReason: reason
                )
                self?.detailView.configure(with: agent, isOnline: isOnline, offlineReason: reason)
            }
        }
    }

    private func loadChatHistory(_ agentId: String) {
        let enc = agentId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? agentId
        get("\(server)/api/messages/\(enc)") { [weak self] data, _ in
            guard let d = data,
                  let json = try? JSONSerialization.jsonObject(with: d) as? [String:Any],
                  let msgs = json["messages"] as? [[String:Any]] else { return }
            let decoded = msgs.compactMap { dict -> ChatMessage? in
                guard let jd = try? JSONSerialization.data(withJSONObject: dict, options: .fragmentsAllowed),
                      let m = try? JSONDecoder().decode(ChatMessage.self, from: jd) else { return nil }
                return m
            }
            DispatchQueue.main.async {
                self?.chatView.loadMessages(decoded, consoleId: self?.consoleId ?? "")
            }
        }
    }

    // MARK: - WebSocket
    private func connectWebSocket() {
        guard let url = URL(string: "\(wsServer)?console=1") else { return }
        wsTask = URLSession.shared.webSocketTask(with: url)
        wsTask?.resume()

        // Register as console
        let reg: [String: Any] = ["type":"register","payload":["id":consoleId,"name":"Console","type":"console" as Any]]
        if let d = try? JSONSerialization.data(withJSONObject: reg, options: .fragmentsAllowed),
           let s = String(data: d, encoding: .utf8) {
            wsTask?.send(.string(s)) { _ in }
        }

        wsTask?.receive { [weak self] result in
            switch result {
            case .success(let msg):
                if case .string(let text) = msg {
                    self?.handleWSMessage(text)
                }
                self?.connectWebSocket() // continue listening
            case .failure:
                DispatchQueue.main.async {
                    self?.wsConnected = false
                    self?.statusDot.layer?.backgroundColor = Theme.shared.danger.cgColor
                    self?.statusLabel.stringValue = L10n.t("disconnected")
                }
            }
        }
    }

    private func handleWSMessage(_ text: String) {
        guard let d = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: d) as? [String:Any] else { return }
        let type = json["type"] as? String ?? ""
        if type == "message", let from = json["from"] as? String {
            let payload = json["payload"] as? [String:Any]
            let txt = payload?["text"] as? String ?? ""
            DispatchQueue.main.async { [weak self] in
                self?.chatView.addReceivedMsg(txt, from: from)
            }
        }
    }

    // MARK: - HTTP Helpers
    private func get(_ urlStr: String, method: String = "GET", body: [String:Any]? = nil, completion: @escaping (Data?, URLResponse?) -> Void) {
        guard let url = URL(string: urlStr) else { completion(nil, nil); return }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let b = body { req.httpBody = try? JSONSerialization.data(withJSONObject: b, options: .fragmentsAllowed) }
        URLSession.shared.dataTask(with: req) { data, resp, _ in completion(data, resp) }.resume()
    }

    private func post(_ urlStr: String, method: String = "POST", body: [String:Any]? = nil, completion: @escaping (Data?, URLResponse?) -> Void) {
        get(urlStr, method: method, body: body, completion: completion)
    }
}

// MARK: - Table DataSource & Delegate
extension ConsoleViewController: NSTableViewDataSource, NSTableViewDelegate {
    func numberOfRows(in tv: NSTableView) -> Int {
        return tv == agentList ? agents.count : pendingAgents.count
    }

    func tableView(_ tv: NSTableView, viewFor col: NSTableColumn?, row: Int) -> NSView? {
        let agent = tv == agentList ? agents[row] : pendingAgents[row]
        let isPending = tv == pendingList
        let cell = AgentRowView()
        cell.configure(with: agent, isPending: isPending, width: tv.frame.width - 12)
        cell.onConfirm = { [weak self] in self?.confirmAgent(agent.id) }
        cell.onReject = { [weak self] in self?.rejectAgent(agent.id) }
        return cell
    }

    func tableViewSelectionDidChange(_ notification: Notification) {
        guard let tv = notification.object as? NSTableView else { return }
        if tv == agentList {
            let row = tv.selectedRow
            if row >= 0 && row < agents.count {
                let agent = agents[row]
                loadAgentDetail(agent.id)
                loadChatHistory(agent.id)
            }
        }
    }

    private func confirmAgent(_ id: String) {
        let enc = id.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? id
        post("\(server)/api/agents/\(enc)/confirm", method: "POST") { [weak self] _, _ in
            DispatchQueue.main.async {
                self?.chatView.addSystemMsg("\(L10n.t("confirm_success")): \(id)")
                self?.loadData()
            }
        }
    }

    private func rejectAgent(_ id: String) {
        let enc = id.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? id
        post("\(server)/api/agents/\(enc)/reject", method: "POST") { [weak self] _, _ in
            DispatchQueue.main.async {
                self?.chatView.addSystemMsg("已拒绝: \(id)")
                self?.loadData()
            }
        }
    }
}

// MARK: - Agent Row View
class AgentRowView: NSTableCellView {
    var onConfirm: (() -> Void)?
    var onReject: (() -> Void)?

    override init(frame fr: NSRect) { super.init(frame: fr); setup() }
    required init?(coder: NSCoder) { fatalError() }

    func setup() {
        wantsLayer = true
        layer?.cornerRadius = 8
    }

    func configure(with agent: Agent, isPending: Bool, width: CGFloat) {
        subviews.forEach { $0.removeFromSuperview() }

        let pad: CGFloat = 10
        let avSize: CGFloat = 34
        let av = NSView(frame: NSRect(x: pad, y: (52-avSize)/2, width: avSize, height: avSize))
        av.wantsLayer = true
        av.layer?.backgroundColor = Theme.shared.accent.cgColor
        av.layer?.cornerRadius = avSize/2
        addSubview(av)

        let ini = NSTextField(labelWithString: String(agent.name.prefix(1)).uppercased())
        ini.font = NSFont.systemFont(ofSize: 13, weight: .bold)
        ini.textColor = .white
        ini.frame = av.bounds; ini.alignment = .center
        av.addSubview(ini)

        let nameL = NSTextField(labelWithString: agent.name)
        nameL.font = NSFont.systemFont(ofSize: 13, weight: .semibold)
        nameL.textColor = Theme.shared.textPrimary
        nameL.frame = NSRect(x: pad+avSize+8, y: 28, width: width-pad-avSize-80, height: 16)
        addSubview(nameL)

        let metaL = NSTextField(labelWithString: "\(agent.type) · \(agent.id)")
        metaL.font = NSFont.systemFont(ofSize: 10, weight: .regular)
        metaL.textColor = Theme.shared.textSecondary
        metaL.frame = NSRect(x: pad+avSize+8, y: 10, width: width-pad-avSize-80, height: 14)
        addSubview(metaL)

        if isPending {
            let confirmB = btn("确认", color: Theme.shared.success)
            confirmB.frame = NSRect(x: width-120, y: 14, width: 50, height: 24)
            confirmB.target = self; confirmB.action = #selector(doConfirm)
            confirmB.layer?.cornerRadius = 6; addSubview(confirmB)

            let rejectB = btn("拒绝", color: Theme.shared.danger)
            rejectB.frame = NSRect(x: width-66, y: 14, width: 50, height: 24)
            rejectB.target = self; rejectB.action = #selector(doReject)
            rejectB.layer?.cornerRadius = 6; addSubview(rejectB)
        } else {
            let dot = NSView()
            dot.wantsLayer = true
            dot.layer?.cornerRadius = 5
            dot.layer?.backgroundColor = agent.status == "online" ? Theme.shared.success.cgColor : Theme.shared.textSecondary.cgColor
            dot.frame = NSRect(x: width-18, y: (52-10)/2, width: 10, height: 10)
            addSubview(dot)
        }
    }

    @objc private func doConfirm() { onConfirm?() }
    @objc private func doReject() { onReject?() }

    private func btn(_ title: String, color: NSColor) -> NSButton {
        let b = NSButton(title: title, target: nil, action: nil)
        b.bezelStyle = .rounded
        b.wantsLayer = true
        b.layer?.backgroundColor = color.cgColor
        b.contentTintColor = .white
        b.font = NSFont.systemFont(ofSize: 11, weight: .semibold)
        return b
    }
}

// MARK: - Agent Detail View
class AgentDetailView: NSView {
    var onPing: (() -> Void)?
    var onStart: (() -> Void)?

    private var avatarView: NSView!
    private var nameLabel: NSTextField!
    private var typeLabel: NSTextField!
    private var statusBadge: NSView!
    private var statusText: NSTextField!
    private var lastSeenLabel: NSTextField!
    private var capLabel: NSTextField!
    private var offlineLabel: NSTextField!
    private var pingBtn: NSButton!
    private var startBtn: NSButton!
    private var chatTitleLabel: NSTextField!

    override init(frame fr: NSRect) {
        super.init(frame: fr)
        setup()
    }
    required init?(coder: NSCoder) { fatalError() }

    private func setup() {
        avatarView = NSView(frame: NSRect(x: 14, y: 130, width: 40, height: 40))
        avatarView.wantsLayer = true
        avatarView.layer?.backgroundColor = Theme.shared.accent.cgColor
        avatarView.layer?.cornerRadius = 20
        addSubview(avatarView)

        nameLabel = NSTextField(labelWithString: "")
        nameLabel.font = NSFont.systemFont(ofSize: 18, weight: .bold)
        nameLabel.textColor = Theme.shared.textPrimary
        nameLabel.frame = NSRect(x: 64, y: 138, width: 200, height: 22)
        addSubview(nameLabel)

        typeLabel = NSTextField(labelWithString: "")
        typeLabel.font = NSFont.systemFont(ofSize: 12, weight: .regular)
        typeLabel.textColor = Theme.shared.textSecondary
        typeLabel.frame = NSRect(x: 64, y: 118, width: 150, height: 16)
        addSubview(typeLabel)

        statusBadge = NSView(frame: NSRect(x: 64, y: 90, width: 60, height: 20))
        statusBadge.wantsLayer = true
        statusBadge.layer?.cornerRadius = 10
        addSubview(statusBadge)

        statusText = NSTextField(labelWithString: "")
        statusText.font = NSFont.systemFont(ofSize: 11, weight: .semibold)
        statusText.frame = statusBadge.bounds
        statusText.alignment = .center
        statusBadge.addSubview(statusText)

        lastSeenLabel = NSTextField(labelWithString: "")
        lastSeenLabel.font = NSFont.systemFont(ofSize: 11, weight: .regular)
        lastSeenLabel.textColor = Theme.shared.textSecondary
        lastSeenLabel.frame = NSRect(x: 64, y: 68, width: 200, height: 14)
        addSubview(lastSeenLabel)

        capLabel = NSTextField(labelWithString: "")
        capLabel.font = NSFont.systemFont(ofSize: 11, weight: .regular)
        capLabel.textColor = Theme.shared.textSecondary
        capLabel.frame = NSRect(x: 14, y: 46, width: 280, height: 14)
        addSubview(capLabel)

        offlineLabel = NSTextField(labelWithString: "")
        offlineLabel.font = NSFont.systemFont(ofSize: 11, weight: .regular)
        offlineLabel.textColor = Theme.shared.danger
        offlineLabel.frame = NSRect(x: 14, y: 26, width: 280, height: 14)
        addSubview(offlineLabel)

        // Buttons on right side
        chatTitleLabel = NSTextField(labelWithString: L10n.t("chat_with"))
        chatTitleLabel.font = NSFont.systemFont(ofSize: 12, weight: .semibold)
        chatTitleLabel.textColor = Theme.shared.textSecondary
        chatTitleLabel.frame = NSRect(x: 400, y: 148, width: 200, height: 16)
        addSubview(chatTitleLabel)

        pingBtn = NSButton(title: L10n.t("ping_agent"), target: nil, action: #selector(doPing))
        pingBtn.bezelStyle = .rounded
        pingBtn.wantsLayer = true
        pingBtn.layer?.cornerRadius = 6
        pingBtn.font = NSFont.systemFont(ofSize: 12, weight: .medium)
        pingBtn.frame = NSRect(x: 400, y: 108, width: 90, height: 28)
        addSubview(pingBtn)

        startBtn = NSButton(title: L10n.t("start_agent"), target: nil, action: #selector(doStart))
        startBtn.bezelStyle = .rounded
        startBtn.wantsLayer = true
        startBtn.layer?.backgroundColor = Theme.shared.success.cgColor
        startBtn.layer?.cornerRadius = 6
        startBtn.contentTintColor = .white
        startBtn.font = NSFont.systemFont(ofSize: 12, weight: .semibold)
        startBtn.frame = NSRect(x: 498, y: 108, width: 100, height: 28)
        addSubview(startBtn)
    }

    func configure(with agent: Agent, isOnline: Bool, offlineReason: String?) {
        nameLabel.stringValue = agent.name
        typeLabel.stringValue = "\(agent.type) · \(agent.id)"
        statusBadge.layer?.backgroundColor = isOnline ? Theme.shared.success.withAlphaComponent(0.2).cgColor : Theme.shared.danger.withAlphaComponent(0.2).cgColor
        statusText.stringValue = isOnline ? L10n.t("online_") : L10n.t("offline_")
        statusText.textColor = isOnline ? Theme.shared.success : Theme.shared.danger
        lastSeenLabel.stringValue = agent.lastSeen != nil ? "\(L10n.t("last_seen")): \(agent.lastSeen!)" : ""
        capLabel.stringValue = agent.capabilities != nil ? "\(L10n.t("capabilities")): \(agent.capabilities!.joined(separator: ", "))" : ""
        offlineLabel.stringValue = offlineReason ?? ""
    }

    @objc private func doPing() { onPing?() }
    @objc private func doStart() { onStart?() }

    func refreshLabels() {
        chatTitleLabel.stringValue = L10n.t("chat_with")
        pingBtn.title = L10n.t("ping_agent")
        startBtn.title = L10n.t("start_agent")
    }

    func applyTheme() {
        avatarView.layer?.backgroundColor = Theme.shared.accent.cgColor
        nameLabel.textColor = Theme.shared.textPrimary
        typeLabel.textColor = Theme.shared.textSecondary
        lastSeenLabel.textColor = Theme.shared.textSecondary
        capLabel.textColor = Theme.shared.textSecondary
        offlineLabel.textColor = Theme.shared.danger
        chatTitleLabel.textColor = Theme.shared.textSecondary
    }
}

// MARK: - Chat Panel View
class ChatPanelView: NSView {
    var onSend: ((String) -> Void)?

    private var scrollView: NSScrollView!
    private var contentView: NSView!
    private var inputField: NSTextField!
    private var sendBtn: NSButton!
    private var placeholder: NSTextField!
    private var noChatLabel: NSTextField!
    private var messages: [(String, String, Bool)] = [] // (text, time, isSent)

    override init(frame fr: NSRect) {
        super.init(frame: fr)
        setup()
    }
    required init?(coder: NSCoder) { fatalError() }

    private func setup() {
        // Messages area
        scrollView = NSScrollView()
        scrollView.hasVerticalScroller = true
        scrollView.drawsBackground = false
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(scrollView)

        contentView = NSView()
        contentView.wantsLayer = true
        scrollView.documentView = contentView

        noChatLabel = NSTextField(labelWithString: L10n.t("no_chat"))
        noChatLabel.font = NSFont.systemFont(ofSize: 14, weight: .medium)
        noChatLabel.textColor = Theme.shared.textSecondary
        noChatLabel.alignment = .center
        noChatLabel.translatesAutoresizingMaskIntoConstraints = false
        addSubview(noChatLabel)

        // Input area
        let inputBg = NSView()
        inputBg.wantsLayer = true
        inputBg.layer?.cornerRadius = 8
        inputBg.layer?.borderWidth = 1
        inputBg.layer?.borderColor = Theme.shared.border.cgColor
        inputBg.translatesAutoresizingMaskIntoConstraints = false
        addSubview(inputBg)

        inputField = NSTextField()
        inputField.placeholderString = L10n.t("type_placeholder")
        inputField.isBordered = false
        inputField.focusRingType = .none
        inputField.font = NSFont.systemFont(ofSize: 13)
        inputField.textColor = Theme.shared.textPrimary
        inputField.backgroundColor = .clear
        inputField.translatesAutoresizingMaskIntoConstraints = false
        inputField.delegate = self
        inputBg.addSubview(inputField)

        sendBtn = NSButton(title: L10n.t("send"), target: self, action: #selector(sendMsg))
        sendBtn.bezelStyle = .rounded
        sendBtn.wantsLayer = true
        sendBtn.layer?.backgroundColor = Theme.shared.accent.cgColor
        sendBtn.layer?.cornerRadius = 6
        sendBtn.contentTintColor = .white
        sendBtn.font = NSFont.systemFont(ofSize: 12, weight: .semibold)
        sendBtn.translatesAutoresizingMaskIntoConstraints = false
        addSubview(sendBtn)

        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: topAnchor, constant: 8),
            scrollView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 8),
            scrollView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -8),
            scrollView.bottomAnchor.constraint(equalTo: inputBg.topAnchor, constant: -8),

            noChatLabel.centerXAnchor.constraint(equalTo: scrollView.centerXAnchor),
            noChatLabel.centerYAnchor.constraint(equalTo: scrollView.centerYAnchor),

            inputBg.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 8),
            inputBg.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -8),
            inputBg.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -10),
            inputBg.heightAnchor.constraint(equalToConstant: 40),

            inputField.leadingAnchor.constraint(equalTo: inputBg.leadingAnchor, constant: 12),
            inputField.trailingAnchor.constraint(equalTo: sendBtn.leadingAnchor, constant: -8),
            inputField.centerYAnchor.constraint(equalTo: inputBg.centerYAnchor),

            sendBtn.trailingAnchor.constraint(equalTo: inputBg.trailingAnchor, constant: -10),
            sendBtn.centerYAnchor.constraint(equalTo: inputBg.centerYAnchor),
            sendBtn.widthAnchor.constraint(equalToConstant: 64),
        ])
    }

    func loadMessages(_ msgs: [ChatMessage], consoleId: String) {
        messages.removeAll()
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss"
        for m in msgs {
            let time = m.timestamp != nil ? formatter.string(from: Date()) : ""
            let isSent = m.from == consoleId
            messages.append((m.text, time, isSent))
        }
        renderMessages()
    }

    func addSentMsg(_ text: String) {
        let formatter = DateFormatter(); formatter.dateFormat = "HH:mm:ss"
        messages.append((text, formatter.string(from: Date()), true))
        renderMessages()
    }

    func addReceivedMsg(_ text: String, from: String) {
        let formatter = DateFormatter(); formatter.dateFormat = "HH:mm:ss"
        messages.append(("\(from): \(text)", formatter.string(from: Date()), false))
        renderMessages()
    }

    func addSystemMsg(_ text: String) {
        let formatter = DateFormatter(); formatter.dateFormat = "HH:mm:ss"
        messages.append(("[系统] \(text)", formatter.string(from: Date()), false))
        renderMessages()
    }

    private func renderMessages() {
        contentView.subviews.forEach { $0.removeFromSuperview() }

        noChatLabel.isHidden = !messages.isEmpty

        let scrollH = scrollView.frame.height
        let rowH: CGFloat = 32
        let totalH = max(CGFloat(messages.count) * rowH + 16, scrollH)
        contentView.frame = NSRect(x: 0, y: 0, width: scrollView.frame.width, height: totalH)

        for (i, msg) in messages.enumerated() {
            let (text, time, isSent) = msg
            let row = NSView(frame: NSRect(x: 0, y: totalH - CGFloat(i+1)*rowH + (rowH-24)/2, width: contentView.frame.width, height: 24))

            let timeL = NSTextField(labelWithString: time)
            timeL.font = NSFont.monospacedDigitSystemFont(ofSize: 10, weight: .regular)
            timeL.textColor = Theme.shared.textSecondary
            timeL.frame = NSRect(x: 0, y: 4, width: 46, height: 16)
            row.addSubview(timeL)

            let msgL = NSTextField(labelWithString: text)
            msgL.font = NSFont.systemFont(ofSize: 12, weight: isSent ? .semibold : .regular)
            msgL.textColor = isSent ? Theme.shared.accent : Theme.shared.textPrimary
            msgL.lineBreakMode = .byTruncatingTail
            msgL.frame = NSRect(x: 50, y: 4, width: contentView.frame.width - 60, height: 16)
            row.addSubview(msgL)

            contentView.addSubview(row)
        }
    }

    @objc private func sendMsg() {
        let text = inputField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        onSend?(text)
        inputField.stringValue = ""
    }

    func refreshLabels() {
        inputField.placeholderString = L10n.t("type_placeholder")
        sendBtn.title = L10n.t("send")
        noChatLabel.stringValue = L10n.t("no_chat")
    }

    func applyTheme() {
        inputField.textColor = Theme.shared.textPrimary
    }
}

extension ChatPanelView: NSTextFieldDelegate {
    func control(_ control: NSControl, textView: NSTextView, doCommandBy commandSelector: Selector) -> Bool {
        if commandSelector == #selector(insertNewline(_:)) {
            sendMsg()
            return true
        }
        return false
    }
}

// MARK: - Stat Card
class StatCard: NSView {
    let id: String
    let key: String
    private let iconLabel: NSTextField
    private let numLabel: NSTextField
    private let descLabel: NSTextField

    init(id: String, icon: String) {
        self.id = id
        self.key = icon
        iconLabel = NSTextField(labelWithString: icon)
        numLabel = NSTextField(labelWithString: "-")
        descLabel = NSTextField(labelWithString: "")
        super.init(frame: .zero)
        setup()
    }
    required init?(coder: NSCoder) { fatalError() }

    private func setup() {
        wantsLayer = true
        layer?.cornerRadius = 10
        layer?.backgroundColor = Theme.shared.cardBg.cgColor
        layer?.borderWidth = 1
        layer?.borderColor = Theme.shared.border.cgColor

        iconLabel.font = NSFont.systemFont(ofSize: 18)
        iconLabel.alignment = .center
        iconLabel.translatesAutoresizingMaskIntoConstraints = false
        addSubview(iconLabel)

        numLabel.font = NSFont.systemFont(ofSize: 22, weight: .bold)
        numLabel.textColor = Theme.shared.accent
        numLabel.alignment = .center
        numLabel.translatesAutoresizingMaskIntoConstraints = false
        addSubview(numLabel)

        descLabel.font = NSFont.systemFont(ofSize: 10, weight: .regular)
        descLabel.textColor = Theme.shared.textSecondary
        descLabel.alignment = .center
        descLabel.translatesAutoresizingMaskIntoConstraints = false
        addSubview(descLabel)

        NSLayoutConstraint.activate([
            iconLabel.centerXAnchor.constraint(equalTo: centerXAnchor),
            iconLabel.topAnchor.constraint(equalTo: topAnchor, constant: 8),
            numLabel.centerXAnchor.constraint(equalTo: centerXAnchor),
            numLabel.topAnchor.constraint(equalTo: iconLabel.bottomAnchor, constant: 2),
            descLabel.centerXAnchor.constraint(equalTo: centerXAnchor),
            descLabel.topAnchor.constraint(equalTo: numLabel.bottomAnchor, constant: 0),
        ])
    }

    func setVal(_ v: Int) { numLabel.stringValue = "\(v)" }
    func refreshLabel(_ t: String) { descLabel.stringValue = t }
    func applyTheme() {
        layer?.backgroundColor = Theme.shared.cardBg.cgColor
        layer?.borderColor = Theme.shared.border.cgColor
        numLabel.textColor = Theme.shared.accent
        descLabel.textColor = Theme.shared.textSecondary
    }
}

