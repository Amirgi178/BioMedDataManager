import os, sys, json, hashlib, shutil
from datetime import datetime

class BMDMSystem:
    BMDM = ".bmdm"
    CONFIG = f"{BMDM}/config.json"
    INDEX = f"{BMDM}/index.json"
    OBJECTS = f"{BMDM}/objects"
    HIST = f"{BMDM}/activity.hist"

    def boot(self):
        if os.path.exists(self.BMDM):
            print("Already initialized.")
            return
        os.makedirs(self.OBJECTS)
        json.dump({}, open(self.CONFIG, 'w'))
        json.dump([], open(self.INDEX, 'w'))
        open(self.HIST, 'w').close()
        print("BMDM ready.")

    def config(self, args):
        cfg = json.load(open(self.CONFIG))
        if '--user.name' in args:
            cfg['name'] = args[args.index('--user.name') + 1]
        if '--user.email' in args:
            cfg['email'] = args[args.index('--user.email') + 1]
        json.dump(cfg, open(self.CONFIG, 'w'), indent=2)
        print("Config saved.")

    def parse_meta(self, path):
        if path.endswith(".txt"):
            p = os.path.basename(path).replace(".txt", "").split('_')
            if len(p) < 4:
                return None
            return {"patient_id": p[0], "study_date": p[1], "modality": p[2], "filename": p[3]}
        elif path.endswith(".json"):
            d = json.load(open(path))
            return {**d, "filename": os.path.basename(path)}

    def admit(self, paths):
        idx = json.load(open(self.INDEX))
        file_list = [paths[0]] if os.path.isfile(paths[0]) else [f"{paths[0]}/{f}" for f in os.listdir(paths[0])]
        for path in file_list:
            meta = self.parse_meta(path)
            if not meta:
                continue
            content = open(path).read()
            meta['entry_id'] = hashlib.md5(content.encode()).hexdigest()
            shutil.copy(path, f"{self.OBJECTS}/{meta['entry_id']}")
            idx.append(meta)
            with open(self.HIST, 'a') as h:
                h.write(f"{datetime.now()} | ADD_FILE | {meta['entry_id']}\n")
        json.dump(idx, open(self.INDEX, 'w'), indent=2)
        print("Admit done.")

    def stats(self):
        idx = json.load(open(self.INDEX))
        print(f"Entries: {len(idx)}\nModalities: {', '.join(set(i['modality'] for i in idx))}")

    def tag(self, args):
        target = args[0]
        add = args[args.index('--add-tag') + 1] if '--add-tag' in args else None
        rem = args[args.index('--remove-tag') + 1] if '--remove-tag' in args else None
        idx = json.load(open(self.INDEX))
        for e in idx:
            if e.get('entry_id') == target or e.get('filename') == target:
                if add:
                    k, v = add.split('=')
                    e[k] = v
                    open(self.HIST, 'a').write(f"{datetime.now()} | TAG | {e['entry_id']} | {k}={v}\n")
                if rem and rem in e:
                    del e[rem]
                    open(self.HIST, 'a').write(f"{datetime.now()} | REMOVE_TAG | {e['entry_id']} | {rem}\n")
        json.dump(idx, open(self.INDEX, 'w'), indent=2)
        print("Tag updated.")

    def find(self, args):
        flt = {}
        idx = json.load(open(self.INDEX))
        for k in ['--patient-id', '--modality', '--study-date', '--tag']:
            if k in args:
                val = args[args.index(k) + 1]
                flt.update(
                    dict([val.split('=')]) if k == '--tag' else {k[2:].replace('-', '_'): val}
                )
        for e in idx:
            if all(e.get(k) == v for k, v in flt.items()):
                print(json.dumps(e, indent=2))

    def hist(self, args):
        lines = open(self.HIST).readlines()
        if '--limit' in args:
            lines = lines[-int(args[args.index('--limit') + 1]):]
        print(''.join(lines))


def main():
    system = BMDMSystem()
    if len(sys.argv) < 2:
        print(" Please provide a command. Example: python bmdm.py boot")
        exit()

    if not os.path.exists(system.BMDM) and sys.argv[1] != 'boot':
        print(" Error: You must run 'boot' first to initialize the system.")
        exit()

    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'boot':
        system.boot()
    elif cmd == 'config':
        system.config(args)
    elif cmd == 'admit':
        system.admit(args)
    elif cmd == 'stats':
        system.stats()
    elif cmd == 'tag':
        system.tag(args)
    elif cmd == 'find':
        system.find(args)
    elif cmd == 'hist':
        system.hist(args)
    else:
        print("Unknown command")

if __name__ == '__main__':
    main()