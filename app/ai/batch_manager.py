class BatchManager:
    def __init__(self, max_items=40, max_characters=24000): self.max_items=max(1,int(max_items)); self.max_characters=max(1000,int(max_characters))
    def split(self, entries: list[dict]) -> list[list[dict]]:
        batches=[]; current=[]; size=0
        for entry in entries:
            length=len(str(entry.get("text", "")))+len(str(entry.get("id", "")))
            if current and (len(current)>=self.max_items or size+length>self.max_characters): batches.append(current); current=[]; size=0
            current.append(entry); size+=length
        if current: batches.append(current)
        return batches
