import AppKit

class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var vc: ConsoleViewController!

    func applicationDidFinishLaunching(_ n: Notification) {
        vc = ConsoleViewController()

        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1280, height: 820),
            styleMask: [.titled,.closable,.miniaturizable,.resizable,.fullSizeContentView],
            backing: .buffered, defer: false
        )
        window.title = L10n.t("title")
        window.minSize = NSSize(width: 900, height: 600)
        window.contentViewController = vc
        window.center()
        window.makeKeyAndOrderFront(nil)
        setupMenu()
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_: NSApplication) -> Bool { true }

    private func setupMenu() {
        let m = NSMenu()
        NSApp.mainMenu = m

        let appItem = NSMenuItem(); m.addItem(appItem)
        let appMenu = NSMenu(); appItem.submenu = appMenu
        appMenu.addItem(withTitle: "About Agent Mesh Console", action: nil, keyEquivalent: "")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "Quit", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")

        let viewItem = NSMenuItem(); m.addItem(viewItem)
        let viewMenu = NSMenu(title: "View"); viewItem.submenu = viewMenu
        viewMenu.addItem(withTitle: L10n.t("refresh"), action: #selector(ConsoleViewController.doRefresh), keyEquivalent: "r")

        let winItem = NSMenuItem(); m.addItem(winItem)
        let winMenu = NSMenu(title: "Window"); winItem.submenu = winMenu
        winMenu.addItem(withTitle: "Minimize", action: #selector(NSWindow.miniaturize(_:)), keyEquivalent: "m")
        winMenu.addItem(withTitle: "Zoom", action: #selector(NSWindow.performZoom(_:)), keyEquivalent: "")
    }
}
