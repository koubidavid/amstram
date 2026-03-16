class SnapshotPipeline:
    def process_item(self, item, spider):
        from scrapper.items import AgenceItem
        if isinstance(item, AgenceItem):
            item["_create_snapshot"] = True
        return item
