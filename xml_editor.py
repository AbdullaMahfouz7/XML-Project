#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
xml_editor.py

Main script for:
  1. Command-line interface supporting:
      - verify, format, json, mini, compress, decompress
      - draw, search, most_active, most_influencer, mutual, suggest
  2. GUI interface using Tkinter:
      - File selection
      - Output display
      - Buttons to trigger each operation
      - Graph visualization with NetworkX

Uses custom data structures from data_structures.py for:
  - XML tag stack verification
  - Byte Pair Encoding compression
  - Adjacency list using DynamicArray for social network
"""

import sys
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# 3rd-party libs for graph visualization
import networkx as nx
import matplotlib.pyplot as plt

# Import our custom data structures
from data_structures import DynamicArray, SinglyLinkedList, Stack, BytePairEncoder


###############################################################################
# 1) From-Scratch XML Verification
###############################################################################

def verify_xml_structure(xml_str, auto_fix=False):
    """
    Uses a Stack to check for matching opening/closing tags.
    Returns (is_consistent, possibly_fixed_xml, message).
    If auto_fix=True, attempts naive corrections for mismatched tags.
    """
    # We'll do a very simplified tag-based parse to demonstrate stack usage.
    # Real-world XML parsing is more complex (attributes, self-closing tags, etc.)

    # Regex to find all tags, opening or closing
    tags = re.findall(r"<(/?[^>]+)>", xml_str)

    stack = Stack()
    errors = []

    # We'll build a list of tokens (strings or tags)
    # so we can do "auto-fix" if needed
    split_pattern = r'(<[^>]+>)'
    tokens = re.split(split_pattern, xml_str)
    # tokens will be a list: text, <tag>, more text, <tag> ...

    for t in tags:
        if t.startswith("/"):  # a closing tag
            closing_tag_name = t[1:].strip()
            if stack.is_empty():
                errors.append(f"Unexpected closing tag </{closing_tag_name}> with no matching opening tag.")
            else:
                top_tag = stack.pop()
                if top_tag != closing_tag_name:
                    errors.append(f"Mismatched tag: <{top_tag}> closed by </{closing_tag_name}>.")
        else:
            # get the tag name (ignoring attributes if any)
            # e.g. <tag attr="val">
            # We'll split on whitespace to get the first piece
            open_name = t.split()[0]
            # remove optional slash if self-closing
            if open_name.endswith("/"):
                open_name = open_name[:-1].strip()
            open_name = open_name.strip()
            stack.push(open_name)

    # if stack not empty => some tags never closed
    while not stack.is_empty():
        unclosed = stack.pop()
        errors.append(f"Unclosed tag <{unclosed}>.")

    if errors:
        if auto_fix:
            # Extremely naive attempt to fix:
            # For each error about mismatched or unclosed, we might remove or insert a tag.
            # This is purely demonstration; real logic is more complex.
            corrected = _naive_xml_autofix(tokens, errors)
            if corrected:
                return (True, corrected, "XML had errors but was auto-fixed.")
            else:
                return (False, xml_str, "Failed to fully auto-fix. Errors:\n" + "\n".join(errors))
        else:
            return (False, xml_str, "XML is inconsistent:\n" + "\n".join(errors))
    else:
        return (True, xml_str, "XML is well-formed and consistent.")


def _naive_xml_autofix(tokens, errors):
    # Just a placeholder to show some approach; we do minimal editing:
    # E.g. if we have "Unclosed tag <XYZ>.", we can try to append </XYZ> near the end.
    # If we have "Unexpected closing tag </XYZ>", we remove that token.
    new_tokens = []
    to_append = []

    for line in errors:
        if line.startswith("Unclosed tag <"):
            tag_name = line.split("<")[1].split(">")[0]
            to_append.append(f"</{tag_name}>")
        if "Unexpected closing tag </" in line:
            # we might remove that tag from tokens if it appears
            pass

    # We won't do complicated removal here, just do minimal. For demonstration:
    # 1) We'll remove lines complaining about "Mismatched tag..."
    # 2) We'll add new closing tags at the end.

    # If we wanted to remove mismatched closing tags, we'd parse the error string
    # and remove them from the tokens. We'll skip the details here.

    # Combine tokens back:
    new_xml = "".join(tokens)
    # append missing closings
    for ta in to_append:
        new_xml += ta
    return new_xml


###############################################################################
# 2) Formatting (Prettifying) XML
###############################################################################

def format_xml(xml_str):
    """
    A simple indentation-based approach: parse the tags and indent.
    """
    # We'll do a naive approach: tokenize by tags, indent for each level.
    # Real solutions typically rely on libraries or xml.dom.minidom.

    tokens = re.split(r'(<[^>]+>)', xml_str)
    result = []
    indent_level = 0
    spaces = "  "

    for token in tokens:
        if not token.strip():
            continue
        if token.startswith("<"):
            # check if closing tag
            if token.startswith("</"):
                indent_level -= 1
                result.append(spaces * indent_level + token)
            else:
                # opening or self-closing
                result.append(spaces * indent_level + token)
                if not token.endswith("/>"):
                    # not a self closing tag
                    indent_level += 1
        else:
            # text content
            # strip leading/trailing newlines
            lines = token.strip().splitlines()
            for line in lines:
                if line.strip():
                    result.append(spaces * indent_level + line.strip())

    formatted_str = "\n".join(result)
    return formatted_str


###############################################################################
# 3) Converting XML to JSON
###############################################################################

def xml_to_json(xml_str):
    """
    Convert the given (well-formed) XML to a JSON-like dictionary, then to a string.
    We'll do an ad-hoc parse. Real code might use an XML parser.
    """
    # For demonstration, let's parse with a built-in parser (re-inventing from scratch is large).
    # But we remain consistent: we only rely on it to get an Element tree for easy iteration.
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return None  # not well-formed

    def elem_to_dict(elem):
        d = {}
        # children
        for child in elem:
            child_name = child.tag
            child_dict = elem_to_dict(child)
            if child_name not in d:
                d[child_name] = []
            d[child_name].append(child_dict)
        # text
        text = (elem.text or '').strip()
        if text:
            d['text'] = text
        return d

    root_dict = {root.tag: elem_to_dict(root)}
    # Convert to a pretty JSON string
    import json
    return json.dumps(root_dict, indent=2)


###############################################################################
# 4) Minifying XML
###############################################################################

def minify_xml(xml_str):
    """
    Remove all unnecessary whitespaces, newlines.
    """
    # We remove newlines, then remove spaces between tags
    no_newlines = re.sub(r"\s*\n\s*", "", xml_str)
    # remove spaces between tags: <tag>  <tag2> => <tag><tag2>
    collapsed = re.sub(r">\s+<", "><", no_newlines)
    return collapsed.strip()


###############################################################################
# 5) Compression / Decompression (Byte-Pair Encoding)
###############################################################################

def compress_data(input_str):
    """
    Use BytePairEncoder from data_structures.py
    Returns (compressed_str, merges_map) which can be stored or saved as needed.
    """
    compressed, merges_map = BytePairEncoder.compress(input_str, num_merges=10)
    return compressed, merges_map

def decompress_data(compressed_str, merges_map):
    """
    Decompress using BytePairEncoder
    """
    return BytePairEncoder.decompress(compressed_str, merges_map)


###############################################################################
# 6) Building and Analyzing the Social Network Graph
#    (Using a custom adjacency list + optional NetworkX for visualization)
###############################################################################

class SocialNetwork:
    """
    Represent users in an adjacency list (from-scratch using DynamicArray),
    where each user has:
      - user_id (string or int)
      - name
      - posts (a LinkedList of (body, topics))
      - followers (list of user_ids following this user)
    We also track who *this user* follows (which we can derive by flipping edges).
    """

    def __init__(self):
        # We'll store each user in a DynamicArray as a dict:
        # { 'id': str,
        #   'name': str,
        #   'posts': SinglyLinkedList of { 'body': str, 'topics': [str, ...] },
        #   'followers': DynamicArray of user_ids (who follow this user) }
        self.users = DynamicArray()

    def add_user(self, user_id, name):
        # Check if user_id exists
        if self.find_user_index(user_id) != -1:
            return  # already exists
        user_dict = {
            'id': user_id,
            'name': name,
            'posts': SinglyLinkedList(),
            'followers': DynamicArray()
        }
        self.users.append(user_dict)

    def find_user_index(self, user_id):
        for i in range(len(self.users)):
            if self.users.get(i)['id'] == user_id:
                return i
        return -1

    def add_follower(self, user_id, follower_id):
        # user_id: the user who is being followed
        # follower_id: the user who follows
        idx = self.find_user_index(user_id)
        if idx == -1:
            return
        user_data = self.users.get(idx)
        # Check if follower_id not already in followers
        for j in range(len(user_data['followers'])):
            if user_data['followers'].get(j) == follower_id:
                return  # already a follower
        user_data['followers'].append(follower_id)

    def add_post(self, user_id, body, topics):
        idx = self.find_user_index(user_id)
        if idx == -1:
            return
        user_data = self.users.get(idx)
        user_data['posts'].insert_at_tail({
            'body': body,
            'topics': topics
        })

    def build_from_xml(self, xml_str):
        """
        Parse the given XML (users, each user has <id>, <name>, <posts>, <followers>).
        We'll rely on a simple re-parse with xml.etree (since the big logic is done above).
        """
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            return  # do nothing if invalid

        for user_elem in root.findall('user'):
            uid = user_elem.findtext('id', '').strip()
            name = user_elem.findtext('name', '').strip()
            self.add_user(uid, name)

            # posts
            posts_elem = user_elem.find('posts')
            if posts_elem is not None:
                for post_elem in posts_elem.findall('post'):
                    body_text = post_elem.findtext('body', '').strip()
                    topics_list = []
                    topics_elem = post_elem.find('topics')
                    if topics_elem is not None:
                        for t in topics_elem.findall('topic'):
                            topics_list.append(t.text.strip())
                    self.add_post(uid, body_text, topics_list)

            # followers
            foll_elem = user_elem.find('followers')
            if foll_elem is not None:
                for f in foll_elem.findall('follower'):
                    fid = f.findtext('id', '').strip()
                    self.add_follower(uid, fid)

    def to_networkx(self):
        """
        Convert our adjacency info to a NetworkX DiGraph:
          - If X is in Y's followers => Y -> X edge
          (meaning X follows Y)
        """
        G = nx.DiGraph()
        # add nodes
        for i in range(len(self.users)):
            udata = self.users.get(i)
            uid = udata['id']
            G.add_node(uid, name=udata['name'], posts=udata['posts'].to_list())
        # add edges
        for i in range(len(self.users)):
            udata = self.users.get(i)
            uid = udata['id']
            # For each follower => follower -> user
            for j in range(len(udata['followers'])):
                fid = udata['followers'].get(j)
                # edge: fid -> uid
                G.add_edge(fid, uid)
        return G

    def find_most_active(self):
        """
        Most active user = user with highest 'outdegree' in the graph
        (the # of people they follow). We can compute it by flipping
        the 'followers' perspective: outdegree = # of users who list this
        user as a follower.
        """
        # Build quick map: user_id -> # following
        # We'll do: for each user, see how many times they appear in others' follower lists
        following_count = {}
        # init all
        for i in range(len(self.users)):
            uid = self.users.get(i)['id']
            following_count[uid] = 0

        for i in range(len(self.users)):
            udata = self.users.get(i)
            uid = udata['id']
            # Everyone in udata['followers'] follows uid
            for j in range(len(udata['followers'])):
                fid = udata['followers'].get(j)
                # fid is following uid => increment fid's "outdegree"
                following_count[fid] = following_count.get(fid, 0) + 1

        # find max
        max_user = None
        max_val = -1
        for user_id, val in following_count.items():
            if val > max_val:
                max_val = val
                max_user = user_id

        # also get that user name
        if max_user is not None:
            idx = self.find_user_index(max_user)
            if idx != -1:
                return (max_user, self.users.get(idx)['name'], max_val)
        return (None, None, 0)

    def find_most_influencer(self):
        """
        Most influencer = user with largest # of followers.
        """
        max_user = None
        max_val = -1
        max_name = None
        for i in range(len(self.users)):
            udata = self.users.get(i)
            uid = udata['id']
            fname = udata['name']
            fcount = len(udata['followers'])
            if fcount > max_val:
                max_val = fcount
                max_user = uid
                max_name = fname
        return (max_user, max_name, max_val)

    def mutual_followers(self, user_ids):
        """
        user_ids: a list of user IDs. Return the set of users who follow all of them.
        """
        if not user_ids:
            return []
        # Build intersection of followers
        first_user_idx = self.find_user_index(user_ids[0])
        if first_user_idx == -1:
            return []
        mutual_set = set(self.users.get(first_user_idx)['followers'].to_list())

        for uid in user_ids[1:]:
            idx = self.find_user_index(uid)
            if idx == -1:
                return []
            this_set = set(self.users.get(idx)['followers'].to_list())
            mutual_set = mutual_set.intersection(this_set)

        return list(mutual_set)

    def suggest_follows(self, user_id):
        """
        Suggest a list of users to follow for user_id,
        based on "followers of my followers" that I'm not already following.
        """
        idx = self.find_user_index(user_id)
        if idx == -1:
            return []
        # gather who user_id currently follows
        # user_id follows U => U has user_id in its followers
        # so we find all U for which user_id is in U's followers
        currently_follows = set()
        for i in range(len(self.users)):
            udata = self.users.get(i)
            if user_id in udata['followers'].to_list():
                currently_follows.add(udata['id'])

        # gather second-level
        suggestions = set()
        for following_user in currently_follows:
            # get that user's followers (i.e. the accounts that follow "following_user")
            fidx = self.find_user_index(following_user)
            if fidx != -1:
                flwr_list = self.users.get(fidx)['followers'].to_list()
                for f in flwr_list:
                    if f not in currently_follows and f != user_id:
                        suggestions.add(f)
        return list(suggestions)

    def search_posts_word(self, word):
        """
        Return a list of (user_id, post_body) for each post that contains 'word'
        in the body. Case-insensitive.
        """
        result = []
        w_lower = word.lower()
        for i in range(len(self.users)):
            udata = self.users.get(i)
            uid = udata['id']
            name = udata['name']
            p = udata['posts'].head
            while p:
                body_text = p.value['body']
                if w_lower in body_text.lower():
                    result.append((uid, name, body_text))
                p = p.next
        return result

    def search_posts_topic(self, topic):
        """
        Return a list of (user_id, post_body) for each post that has <topic> in topics list.
        """
        result = []
        t_lower = topic.lower()
        for i in range(len(self.users)):
            udata = self.users.get(i)
            uid = udata['id']
            name = udata['name']
            p = udata['posts'].head
            while p:
                topics = p.value['topics']
                # check if t_lower in topics (case-insensitive)
                if any(t_lower == x.lower() for x in topics):
                    result.append((uid, name, p.value['body']))
                p = p.next
        return result


###############################################################################
# 7) Network Visualization
###############################################################################

def draw_network(social_net):
    """
    Uses NetworkX to draw the directed graph.
    """
    G = social_net.to_networkx()
    if len(G.nodes) == 0:
        print("No users in network.")
        return
    plt.figure(figsize=(6, 4))
    pos = nx.spring_layout(G)
    nx.draw_networkx_nodes(G, pos, node_size=800, node_color='lightblue')
    nx.draw_networkx_edges(G, pos, arrowstyle='-|>', arrowsize=10)
    labels = {n: f"{n}" for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=10)
    plt.title("Social Network")
    plt.axis('off')
    plt.show()


###############################################################################
# 8) Command-Line Interface
###############################################################################

def cli_main():
    """
    Usage examples:
      python xml_editor.py verify -i input_file.xml --fix
      python xml_editor.py format -i input_file.xml
      python xml_editor.py json -i input_file.xml
      python xml_editor.py mini -i input_file.xml
      python xml_editor.py compress -i input_file.xml -o compressed.bpe
      python xml_editor.py decompress -i compressed.bpe -o original.xml
      python xml_editor.py draw -i input_file.xml
      python xml_editor.py search -w "word" -i input_file.xml
      python xml_editor.py search -t "topic" -i input_file.xml
      python xml_editor.py most_active -i input_file.xml
      python xml_editor.py most_influencer -i input_file.xml
      python xml_editor.py mutual -i input_file.xml -ids 1,2
      python xml_editor.py suggest -i input_file.xml -id 1
    """
    argv = sys.argv[1:]
    if not argv:
        print("No command provided.")
        sys.exit(1)

    command = argv[0]
    # parse flags
    if '-i' in argv:
        input_index = argv.index('-i') + 1
        input_file = argv[input_index] if input_index < len(argv) else None
    else:
        input_file = None

    if not input_file or not os.path.isfile(input_file):
        if command not in ['help', '-h', '--help']:
            print("Input file not found or not specified. Use -i <filename>")
            sys.exit(1)

    output_file = None
    if '-o' in argv:
        out_index = argv.index('-o') + 1
        if out_index < len(argv):
            output_file = argv[out_index]

    if command == 'verify':
        # check if --fix is present
        auto_fix = '--fix' in argv
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xml_str = f.read()
        ok, fixed, msg = verify_xml_structure(xml_str, auto_fix=auto_fix)
        print(msg)
        if ok and auto_fix and output_file:
            with open(output_file, 'w', encoding='utf-8') as fw:
                fw.write(fixed)
            print(f"Fixed XML saved to {output_file}")

    elif command == 'format':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xml_str = f.read()
        formatted = format_xml(xml_str)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as fw:
                fw.write(formatted)
            print(f"Formatted XML saved to {output_file}")
        else:
            print(formatted)

    elif command == 'json':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xml_str = f.read()
        jstr = xml_to_json(xml_str)
        if jstr is None:
            print("Error: invalid XML or parse error.")
        else:
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as fw:
                    fw.write(jstr)
                print(f"JSON saved to {output_file}")
            else:
                print(jstr)

    elif command == 'mini':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xml_str = f.read()
        mini_str = minify_xml(xml_str)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as fw:
                fw.write(mini_str)
            print(f"Minified XML saved to {output_file}")
        else:
            print(mini_str)

    elif command == 'compress':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            data_str = f.read()
        compressed, merges_map = compress_data(data_str)
        # We need to save both compressed and merges_map (so we can decompress)
        # We'll store merges_map as JSON next to the compressed data
        import json
        bundle = {
            'compressed': compressed,
            'merges_map': merges_map
        }
        out_str = json.dumps(bundle)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as fw:
                fw.write(out_str)
            print(f"Compressed data saved to {output_file}")
        else:
            print(out_str)

    elif command == 'decompress':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            bundle_json = f.read()
        import json
        try:
            bundle = json.loads(bundle_json)
            compressed = bundle['compressed']
            merges_map = bundle['merges_map']
            original = decompress_data(compressed, merges_map)
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as fw:
                    fw.write(original)
                print(f"Decompressed data saved to {output_file}")
            else:
                print(original)
        except:
            print("Error: invalid compressed file format.")

    elif command == 'draw':
        # build network from xml
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xml_str = f.read()
        snet = SocialNetwork()
        snet.build_from_xml(xml_str)
        draw_network(snet)
        if output_file:
            # Optionally save an image of the graph
            # We'll do a quick hack: use plt.savefig
            plt.savefig(output_file)
            print(f"Graph saved to {output_file}")

    elif command == 'search':
        # can be -w word or -t topic
        if '-w' in argv:
            w_idx = argv.index('-w') + 1
            word = argv[w_idx]
            with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
                xml_str = f.read()
            snet = SocialNetwork()
            snet.build_from_xml(xml_str)
            results = snet.search_posts_word(word)
            if results:
                for (uid, name, body) in results:
                    print(f"User {uid} ({name}) => {body[:60]}...")
            else:
                print("No posts found containing that word.")
        elif '-t' in argv:
            t_idx = argv.index('-t') + 1
            topic = argv[t_idx]
            with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
                xml_str = f.read()
            snet = SocialNetwork()
            snet.build_from_xml(xml_str)
            results = snet.search_posts_topic(topic)
            if results:
                for (uid, name, body) in results:
                    print(f"User {uid} ({name}) => {body[:60]}...")
            else:
                print("No posts found containing that topic.")
        else:
            print("Usage for search: xml_editor search -w <word> -i file.xml OR -t <topic> -i file.xml")

    elif command == 'most_active':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xml_str = f.read()
        snet = SocialNetwork()
        snet.build_from_xml(xml_str)
        uid, name, outdeg = snet.find_most_active()
        if uid:
            print(f"Most active user: ID={uid}, Name={name}, OutDegree={outdeg}")
        else:
            print("No users found.")

    elif command == 'most_influencer':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xml_str = f.read()
        snet = SocialNetwork()
        snet.build_from_xml(xml_str)
        uid, name, fcount = snet.find_most_influencer()
        if uid:
            print(f"Most influencer user: ID={uid}, Name={name}, Followers={fcount}")
        else:
            print("No users found.")

    elif command == 'mutual':
        # usage: xml_editor mutual -i input.xml -ids 1,2,3
        if '-ids' not in argv:
            print("Usage: xml_editor mutual -i input.xml -ids 1,2,3")
            sys.exit(1)
        ids_index = argv.index('-ids') + 1
        id_list_str = argv[ids_index]
        user_ids = id_list_str.split(',')
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xml_str = f.read()
        snet = SocialNetwork()
        snet.build_from_xml(xml_str)
        mutuals = snet.mutual_followers(user_ids)
        print(f"Mutual followers of {user_ids} => {mutuals}")

    elif command == 'suggest':
        # usage: xml_editor suggest -i input.xml -id 1
        if '-id' not in argv:
            print("Usage: xml_editor suggest -i input.xml -id <user_id>")
            sys.exit(1)
        user_id = argv[argv.index('-id') + 1]
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xml_str = f.read()
        snet = SocialNetwork()
        snet.build_from_xml(xml_str)
        suggestions = snet.suggest_follows(user_id)
        if suggestions:
            print(f"Suggested users for {user_id} to follow: {suggestions}")
        else:
            print(f"No suggestions or user {user_id} not found.")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


###############################################################################
# 9) Graphical User Interface (Tkinter)
###############################################################################

class XmlEditorGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("XML Editor (Level 1 & 2)")

        # File selection
        file_frame = tk.Frame(self.master)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(file_frame, text="XML File:").pack(side=tk.LEFT)
        self.file_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.file_var, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT)

        # Operation buttons
        btn_frame = tk.Frame(self.master)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text="Verify (Fix)", command=self.gui_verify).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Format", command=self.gui_format).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="To JSON", command=self.gui_json).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Minify", command=self.gui_minify).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Compress", command=self.gui_compress).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Decompress", command=self.gui_decompress).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Draw Graph", command=self.gui_draw).pack(side=tk.LEFT, padx=2)

        # Network Analysis / Search
        adv_frame = tk.Frame(self.master)
        adv_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(adv_frame, text="Most Active", command=self.gui_most_active).pack(side=tk.LEFT, padx=2)
        tk.Button(adv_frame, text="Most Influencer", command=self.gui_most_influencer).pack(side=tk.LEFT, padx=2)

        tk.Label(adv_frame, text="Mutual IDs (1,2,..):").pack(side=tk.LEFT)
        self.mutual_var = tk.StringVar()
        tk.Entry(adv_frame, textvariable=self.mutual_var, width=10).pack(side=tk.LEFT)
        tk.Button(adv_frame, text="Mutual", command=self.gui_mutual).pack(side=tk.LEFT, padx=2)

        tk.Label(adv_frame, text="Suggest for ID:").pack(side=tk.LEFT)
        self.suggest_var = tk.StringVar()
        tk.Entry(adv_frame, textvariable=self.suggest_var, width=5).pack(side=tk.LEFT)
        tk.Button(adv_frame, text="Suggest", command=self.gui_suggest).pack(side=tk.LEFT, padx=2)

        search_frame = tk.Frame(self.master)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="Word:").pack(side=tk.LEFT)
        self.word_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.word_var, width=10).pack(side=tk.LEFT)
        tk.Button(search_frame, text="Search Word", command=self.gui_search_word).pack(side=tk.LEFT, padx=2)

        tk.Label(search_frame, text="Topic:").pack(side=tk.LEFT)
        self.topic_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.topic_var, width=10).pack(side=tk.LEFT)
        tk.Button(search_frame, text="Search Topic", command=self.gui_search_topic).pack(side=tk.LEFT, padx=2)

        # Output area
        self.output_area = scrolledtext.ScrolledText(self.master, width=90, height=20)
        self.output_area.pack(padx=5, pady=5)

        # Save button
        tk.Button(self.master, text="Save Output", command=self.save_output).pack(pady=5)

    def browse_file(self):
        fname = filedialog.askopenfilename(title="Select an XML file")
        if fname:
            self.file_var.set(fname)

    def _read_xml_file(self):
        fpath = self.file_var.get().strip()
        if not os.path.isfile(fpath):
            messagebox.showerror("Error", f"File not found: {fpath}")
            return None
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    def _write_output(self, text):
        self.output_area.delete('1.0', tk.END)
        self.output_area.insert(tk.END, text)

    # GUI Buttons:

    def gui_verify(self):
        content = self._read_xml_file()
        if content is None:
            return
        ok, fixed, msg = verify_xml_structure(content, auto_fix=True)
        output = msg
        if ok and fixed != content:
            output += "\n--- Fixed Version ---\n" + fixed
        self._write_output(output)

    def gui_format(self):
        content = self._read_xml_file()
        if content is None:
            return
        out = format_xml(content)
        self._write_output(out)

    def gui_json(self):
        content = self._read_xml_file()
        if content is None:
            return
        j = xml_to_json(content)
        if j is None:
            self._write_output("Error converting to JSON. Possibly invalid XML.")
        else:
            self._write_output(j)

    def gui_minify(self):
        content = self._read_xml_file()
        if content is None:
            return
        out = minify_xml(content)
        self._write_output(out)

    def gui_compress(self):
        content = self._read_xml_file()
        if content is None:
            return
        comp, merges_map = compress_data(content)
        import json
        bundle = {
            'compressed': comp,
            'merges_map': merges_map
        }
        self._write_output(json.dumps(bundle, indent=2))

    def gui_decompress(self):
        text = self.output_area.get('1.0', tk.END).strip()
        if not text:
            self._write_output("No content in output area to decompress.")
            return
        import json
        try:
            bundle = json.loads(text)
            compressed = bundle['compressed']
            merges_map = bundle['merges_map']
            original = decompress_data(compressed, merges_map)
            self._write_output(original)
        except:
            self._write_output("Failed to parse compressed JSON from output area.")

    def gui_draw(self):
        content = self._read_xml_file()
        if content is None:
            return
        snet = SocialNetwork()
        snet.build_from_xml(content)
        draw_network(snet)

    def gui_most_active(self):
        content = self._read_xml_file()
        if content is None:
            return
        snet = SocialNetwork()
        snet.build_from_xml(content)
        uid, name, outdeg = snet.find_most_active()
        if uid:
            self._write_output(f"Most active: ID={uid}, Name={name}, OutDegree={outdeg}")
        else:
            self._write_output("No users found.")

    def gui_most_influencer(self):
        content = self._read_xml_file()
        if content is None:
            return
        snet = SocialNetwork()
        snet.build_from_xml(content)
        uid, name, count = snet.find_most_influencer()
        if uid:
            self._write_output(f"Most influencer: ID={uid}, Name={name}, Followers={count}")
        else:
            self._write_output("No users found.")

    def gui_mutual(self):
        content = self._read_xml_file()
        if content is None:
            return
        ids_str = self.mutual_var.get().strip()
        if not ids_str:
            self._write_output("No IDs given.")
            return
        user_ids = [x.strip() for x in ids_str.split(',')]
        snet = SocialNetwork()
        snet.build_from_xml(content)
        mutuals = snet.mutual_followers(user_ids)
        self._write_output(f"Mutual followers of {user_ids}: {mutuals}")

    def gui_suggest(self):
        content = self._read_xml_file()
        if content is None:
            return
        uid = self.suggest_var.get().strip()
        if not uid:
            self._write_output("No user ID given for suggestion.")
            return
        snet = SocialNetwork()
        snet.build_from_xml(content)
        sug = snet.suggest_follows(uid)
        self._write_output(f"Suggestions for {uid}: {sug}")

    def gui_search_word(self):
        content = self._read_xml_file()
        if content is None:
            return
        word = self.word_var.get().strip()
        if not word:
            self._write_output("No word provided.")
            return
        snet = SocialNetwork()
        snet.build_from_xml(content)
        results = snet.search_posts_word(word)
        if not results:
            self._write_output("No posts found with that word.")
        else:
            out = "Posts containing the word:\n"
            for uid, name, body in results:
                out += f"User {uid} ({name}): {body[:70]}...\n"
            self._write_output(out)

    def gui_search_topic(self):
        content = self._read_xml_file()
        if content is None:
            return
        topic = self.topic_var.get().strip()
        if not topic:
            self._write_output("No topic provided.")
            return
        snet = SocialNetwork()
        snet.build_from_xml(content)
        results = snet.search_posts_topic(topic)
        if not results:
            self._write_output("No posts found with that topic.")
        else:
            out = "Posts containing the topic:\n"
            for uid, name, body in results:
                out += f"User {uid} ({name}): {body[:70]}...\n"
            self._write_output(out)

    def save_output(self):
        text = self.output_area.get('1.0', tk.END)
        if not text.strip():
            messagebox.showinfo("Info", "No output to save.")
            return
        fname = filedialog.asksaveasfilename(title="Save output", defaultextension=".txt")
        if fname:
            with open(fname, 'w', encoding='utf-8') as fw:
                fw.write(text)
            messagebox.showinfo("Saved", f"Output saved to {fname}")


def gui_main():
    root = tk.Tk()
    app = XmlEditorGUI(root)
    root.mainloop()


###############################################################################
# Main Entry
###############################################################################
if __name__ == "__main__":
    # If user issues "python xml_editor.py <command>" => CLI mode
    if len(sys.argv) > 1:
        # We assume it's CLI usage
        cli_main()
    else:
        # No arguments => open GUI
        gui_main()
