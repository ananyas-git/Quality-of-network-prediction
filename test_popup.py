from win10toast_click import ToastNotifier

notifier = ToastNotifier()
notifier.show_toast("Test Popup", "This is a test notification!", duration=10)
print("Test notification sent!")