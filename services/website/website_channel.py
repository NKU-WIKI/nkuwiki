class WebsiteChannel:
    def __init__(self, name, url, is_active=True):
        self.name = name
        self.url = url
        self.is_active = is_active

    def activate(self):
        self.is_active = True

    def deactivate(self):
        self.is_active = False

    def update_url(self, new_url):
        self.url = new_url

    def __repr__(self):
        return f"<WebsiteChannel {self.name} ({'active' if self.is_active else 'inactive'})>"
