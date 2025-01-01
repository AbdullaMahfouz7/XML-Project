
"""
xml_editor.py

This Logic Implementation can be used from the command line or launched as a GUI(Desktop App).
It uses the custom data structures from data_structures.py and
provides operations for XML verification, formatting, minifying,
JSON conversion, compression/decompression, and social-network analysis.
"""

import sys
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# 3rd-party libraries for visualizing the network
import networkx as nx
import matplotlib.pyplot as plt

from data_structures import DynamicArray, SinglyLinkedList, Stack, BytePairEncoder


###############################################################################
# 1) XML Verification Using a Stack
###############################################################################

def verify_xml_structure(xml_str, auto_fix=False):
    """
    Checks for matching opening and closing tags using our custom Stack.
    Returns (is_consistent, possibly_fixed_string, message).
    If auto_fix=True, tries to fix simpler errors like unclosed tags
    by appending missing closing tags (very naive approach).
    """
    # We'll look for <tag> and </tag> through a regex, then push/pop from a Stack.
    tags = re.findall(r"<(/?[^>]+)>", xml_str)
    stack = Stack()
    errors = []

    # We split the XML into tokens (text or tags) so we can try to fix the content if needed.
    split_pattern = r'(<[^>]+>)'
    tokens = re.split(split_pattern, xml_str)

    for t in tags:
        if t.startswith("/"):
            # This is a closing tag, e.g. </title>
            closing_tag_name = t[1:].strip()
            if stack.is_empty():
                errors.append(f"Unexpected closing tag </{closing_tag_name}> encountered.")
            else:
                top_tag = stack.pop()
                if top_tag != closing_tag_name:
                    errors.append(f"Mismatched tags: <{top_tag}> closed by </{closing_tag_name}>.")
        else:
            # This is an opening tag, e.g. <title>
            # We separate out the tag name from potential attributes
            open_name = t.split()[0]
            # If it's a self-closing tag like <tag .../>, remove the slash at the end.
            if open_name.endswith("/"):
                open_name = open_name[:-1].strip()
            stack.push(open_name.strip())

    # If any tags remain on the stack, they're unclosed.
    while not stack.is_empty():
        unclosed_tag = stack.pop()
        errors.append(f"Unclosed tag <{unclosed_tag}>.")

    if errors:
        if auto_fix:
            fixed_content = _naive_xml_autofix(tokens, errors)
            if fixed_content:
                return (True, fixed_content, "XML had inconsistencies but some were auto-fixed.")
            else:
                return (False, xml_str, "Could not fix all XML issues:\n" + "\n".join(errors))
        else:
            return (False, xml_str, "XML is invalid:\n" + "\n".join(errors))
    else:
        return (True, xml_str, "XML is well-formed.")


def _naive_xml_autofix(tokens, errors):
    """
    A very limited approach to repairing some XML mistakes.
    For example, if there's an 'Unclosed tag <X>', we might add '</X>' near the end.
    """
    new_tokens = []
    to_append = []

    for err in errors:
        if err.startswith("Unclosed tag <"):
            # We'll read the tag name from the message
            tag_name = err.split("<")[1].split(">")[0]
            # We'll plan to append a closing tag at the end of the document
            to_append.append(f"</{tag_name}>")
        elif "Unexpected closing tag </" in err:
            # We might want to remove that closing tag from the tokens
            pass
        elif "Mismatched tags:" in err:
            # This is trickier to fix automatically; we skip it in this simplistic approach
            pass

    # Just recombine everything for now
    new_xml = "".join(tokens)
    for closing in to_append:
        new_xml += closing
    return new_xml


###############################################################################
# 2) Formatting (Prettifying) XML
###############################################################################

def format_xml(xml_str):
    """
    Insert indentation and line breaks to make the XML more readable.
    This is a basic approach that doesn't handle all edge cases.
    """
    tokens = re.split(r'(<[^>]+>)', xml_str)
    result = []
    indent_level = 0
    indent_spaces = "  "

    for token in tokens:
        if not token.strip():
            continue
        if token.startswith("<"):
            # Closing tag?
            if token.startswith("</"):
                indent_level -= 1
                result.append(indent_spaces * indent_level + token)
            else:
                # Opening or self-closing tag
                result.append(indent_spaces * indent_level + token)
                if not token.endswith("/>"):
                    indent_level += 1
        else:
            # Actual text content
            lines = token.strip().splitlines()
            for line in lines:
                if line.strip():
                    result.append(indent_spaces * indent_level + line.strip())

    return "\n".join(result)


###############################################################################
# 3) Converting XML to JSON
###############################################################################

def xml_to_json(xml_str):
    """
    Convert the XML to a JSON-style string using ElementTree.
    If parsing fails, return None.
    """
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return None  # Not well-formed

    def elem_to_dict(elem):
        d = {}
        for child in elem:
            child_name = child.tag
            child_dict = elem_to_dict(child)
            if child_name not in d:
                d[child_name] = []
            d[child_name].append(child_dict)
        text_content = (elem.text or "").strip()
        if text_content:
            d["text"] = text_content
        return d

    root_dict = {root.tag: elem_to_dict(root)}
    import json
    return json.dumps(root_dict, indent=2)


###############################################################################
# 4) Minifying XML
###############################################################################

def minify_xml(xml_str):
    """
    Remove extra whitespace, newlines, and indentation to produce a compact XML.
    """
    no_newline = re.sub(r"\s*\n\s*", "", xml_str)
    collapsed = re.sub(r">\s+<", "><", no_newline)
    return collapsed.strip()


###############################################################################
# 5) Compression / Decompression
###############################################################################

def compress_data(input_str):
    """
    Use BytePairEncoder to compress input_str.
    Returns (compressed_str, merges_map).
    """
    compressed, merges_map = BytePairEncoder.compress(input_str, num_merges=10)
    return compressed, merges_map

def decompress_data(compressed_str, merges_map):
    """
    Decompress using BytePairEncoder with the merges_map.
    """
    return BytePairEncoder.decompress(compressed_str, merges_map)


###############################################################################
# 6) Building and Analyzing the Social Network
###############################################################################

class SocialNetwork:
    """
    Represents users and their connections based on follower data.
    Each user is stored in a DynamicArray with an ID, name, posts, and
    followers (as a DynamicArray of user IDs).
    """

    def __init__(self):
        # Each entry in self.users is a dict:
        # {
        #   'id': str,
        #   'name': str,
        #   'posts': SinglyLinkedList(),  # each post has { 'body': str, 'topics': [list] }
        #   'followers': DynamicArray()   # user IDs of those who follow this user
        # }
        self.users = DynamicArray()

    def add_user(self, user_id, name):
        # Only add the user if it doesn't exist yet.
        if self.find_user_index(user_id) != -1:
            return
        user_info = {
            'id': user_id,
            'name': name,
            'posts': SinglyLinkedList(),
            'followers': DynamicArray()
        }
        self.users.append(user_info)

    def find_user_index(self, user_id):
        # Return the index of the user in self.users, or -1 if not found.
        for i in range(len(self.users)):
            if self.users.get(i)['id'] == user_id:
                return i
        return -1

    def add_follower(self, user_id, follower_id):
        # If user_id is followed by follower_id, store follower_id in user_id's followers.
        idx = self.find_user_index(user_id)
        if idx == -1:
            return
        user_data = self.users.get(idx)
        # Make sure it's not already in the list
        for j in range(len(user_data['followers'])):
            if user_data['followers'].get(j) == follower_id:
                return
        user_data['followers'].append(follower_id)

    def add_post(self, user_id, body, topics):
        # Insert a new post into the user's posts list.
        idx = self.find_user_index(user_id)
        if idx == -1:
            return
        user_data = self.users.get(idx)
        user_data['posts'].insert_at_tail({'body': body, 'topics': topics})

    def build_from_xml(self, xml_str):
        """
        Parse an XML structure for <users>. Each <user>
        has <id>, <name>, <posts>, <followers>, etc.
        """
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            return
        for user_elem in root.findall('user'):
            uid = user_elem.findtext('id', '').strip()
            uname = user_elem.findtext('name', '').strip()
            self.add_user(uid, uname)

            # Extract posts
            posts_elem = user_elem.find('posts')
            if posts_elem is not None:
                for post_elem in posts_elem.findall('post'):
                    body = post_elem.findtext('body', '').strip()
                    topics_list = []
                    topics_elem = post_elem.find('topics')
                    if topics_elem is not None:
                        for t in topics_elem.findall('topic'):
                            topics_list.append(t.text.strip())
                    self.add_post(uid, body, topics_list)

            # Extract followers
            foll_elem = user_elem.find('followers')
            if foll_elem is not None:
                for f in foll_elem.findall('follower'):
                    follower_id = f.findtext('id', '').strip()
                    self.add_follower(uid, follower_id)

    def to_networkx(self):
        """
        Convert the adjacency info to a NetworkX DiGraph for easy visualization.
        For a user U, each follower F => an edge F -> U (meaning F follows U).
        """
        G = nx.DiGraph()
        # Add nodes
        for i in range(len(self.users)):
            data = self.users.get(i)
            G.add_node(data['id'], name=data['name'], posts=data['posts'].to_list())
        # Add edges
        for i in range(len(self.users)):
            data = self.users.get(i)
            uid = data['id']
            for j in range(len(data['followers'])):
                fid = data['followers'].get(j)
                G.add_edge(fid, uid)
        return G

    def find_most_active(self):
        """
        Return the user who follows the most people.
        We'll count how many times each user ID appears in others' followers.
        """
        following_count = {}
        # Initialize all counts
        for i in range(len(self.users)):
            uid = self.users.get(i)['id']
            following_count[uid] = 0

        # If user B is in user A's followers, that means B -> A,
        # so B is following A. We'll increment B's count.
        for i in range(len(self.users)):
            udata = self.users.get(i)
            for j in range(len(udata['followers'])):
                fid = udata['followers'].get(j)
                following_count[fid] = following_count.get(fid, 0) + 1

        # Find the maximum outdegree
        max_user = None
        max_val = -1
        for user_id, val in following_count.items():
            if val > max_val:
                max_val = val
                max_user = user_id

        if max_user is not None:
            idx = self.find_user_index(max_user)
            if idx != -1:
                return (max_user, self.users.get(idx)['name'], max_val)
        return (None, None, 0)

    def find_most_influencer(self):
        """
        Return the user with the highest number of followers.
        """
        max_user = None
        max_val = -1
        max_name = None
        for i in range(len(self.users)):
            udata = self.users.get(i)
            uid = udata['id']
            name = udata['name']
            fcount = len(udata['followers'])
            if fcount > max_val:
                max_val = fcount
                max_user = uid
                max_name = name
        return (max_user, max_name, max_val)

    def mutual_followers(self, user_ids):
        """
        Given a list of user IDs, find all users who follow all of them.
        """
        if not user_ids:
            return []
        idx_first = self.find_user_index(user_ids[0])
        if idx_first == -1:
            return []
        common = set(self.users.get(idx_first)['followers'].to_list())
        for uid in user_ids[1:]:
            idx = self.find_user_index(uid)
            if idx == -1:
                return []
            fset = set(self.users.get(idx)['followers'].to_list())
            common = common.intersection(fset)
        return list(common)

    def suggest_follows(self, user_id):
        """
        Suggest new accounts for user_id to follow based on
        "followers of my followers" that user_id doesn't already follow.
        """
        idx = self.find_user_index(user_id)
        if idx == -1:
            return []
        # Identify who user_id already follows
        # If user_id is in X's followers, that means user_id -> X.
        # So we search for all X where user_id is in X's followers list.
        currently_follows = set()
        for i in range(len(self.users)):
            udata = self.users.get(i)
            if user_id in udata['followers'].to_list():
                currently_follows.add(udata['id'])

        # Then find second-level accounts: the followers of the accounts we follow.
        suggestions = set()
        for followed_user in currently_follows:
            f_idx = self.find_user_index(followed_user)
            if f_idx != -1:
                their_followers = self.users.get(f_idx)['followers'].to_list()
                for fol in their_followers:
                    if fol != user_id and fol not in currently_follows:
                        suggestions.add(fol)
        return list(suggestions)

    def search_posts_word(self, word):
        """
        Find any posts containing 'word' in their body (case-insensitive).
        Returns a list of (user_id, user_name, post_body).
        """
        results = []
        w_lower = word.lower()  # Normalize the word to lowercase
        for i in range(len(self.users)):
            udata = self.users.get(i)
            uid = udata['id']
            uname = udata['name']
            p = udata['posts'].head
            while p:
                body_txt = p.value['body'].strip()  # Clean up whitespace
                if w_lower in body_txt.lower():  # Case-insensitive comparison
                    results.append((uid, uname, body_txt))
                p = p.next
        return results

    def search_posts_topic(self, topic):
        """
        Find any posts that have 'topic' in their topics list (case-insensitive).
        Returns a list of (user_id, user_name, post_body).
        """
        results = []
        t_lower = topic.lower()  # Normalize the topic to lowercase
        for i in range(len(self.users)):
            udata = self.users.get(i)
            uid = udata['id']
            uname = udata['name']
            p = udata['posts'].head
            while p:
                topics_list = [t.strip().lower() for t in p.value['topics']]  # Normalize all topics
                if t_lower in topics_list:  # Check if the normalized topic matches
                    results.append((uid, uname, p.value['body']))
                p = p.next
        return results


def draw_network(social_net):
    """
    Display the social network using NetworkX and matplotlib.
    Edges go from follower to the user they follow.
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
    This function handles command-line usage:
      xml_editor verify -i <file> [--fix] ...
      xml_editor format -i <file> ...
      xml_editor json -i <file> ...
      xml_editor mini -i <file> ...
      xml_editor compress -i <file> ...
      xml_editor decompress -i <file> ...
      xml_editor draw -i <file> ...
      xml_editor search -w <word> -i <file> ...
      xml_editor search -t <topic> -i <file> ...
      xml_editor most_active -i <file> ...
      xml_editor most_influencer -i <file> ...
      xml_editor mutual -i <file> -ids 1,2,...
      xml_editor suggest -i <file> -id 1 ...
    """
    argv = sys.argv[1:]
    if not argv:
        print("No command provided.")
        sys.exit(1)

    command = argv[0]
    if '-i' in argv:
        in_idx = argv.index('-i') + 1
        input_file = argv[in_idx] if in_idx < len(argv) else None
    else:
        input_file = None

    if not input_file or not os.path.isfile(input_file):
        if command not in ['help', '-h', '--help']:
            print("Input file not found or not specified. Use -i <filename>")
            sys.exit(1)

    output_file = None
    if '-o' in argv:
        out_idx = argv.index('-o') + 1
        if out_idx < len(argv):
            output_file = argv[out_idx]

    if command == 'verify':
        auto_fix = '--fix' in argv
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xstr = f.read()
        ok, fixed, msg = verify_xml_structure(xstr, auto_fix=auto_fix)
        print(msg)
        if ok and auto_fix and output_file:
            with open(output_file, 'w', encoding='utf-8') as fw:
                fw.write(fixed)
            print(f"Fixed XML saved to {output_file}")

    elif command == 'format':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xstr = f.read()
        formatted = format_xml(xstr)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as fw:
                fw.write(formatted)
            print(f"Formatted XML saved to {output_file}")
        else:
            print(formatted)

    elif command == 'json':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xstr = f.read()
        j = xml_to_json(xstr)
        if j is None:
            print("Error: invalid XML. Could not convert to JSON.")
        else:
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as fw:
                    fw.write(j)
                print(f"JSON saved to {output_file}")
            else:
                print(j)

    elif command == 'mini':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xstr = f.read()
        mini_str = minify_xml(xstr)
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
            cstr = bundle['compressed']
            merges_map = bundle['merges_map']
            original = decompress_data(cstr, merges_map)
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as fw:
                    fw.write(original)
                print(f"Decompressed data saved to {output_file}")
            else:
                print(original)
        except:
            print("Error: file doesn't seem to be a valid compressed bundle.")

    elif command == 'draw':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xstr = f.read()
        snet = SocialNetwork()
        snet.build_from_xml(xstr)
        draw_network(snet)
        if output_file:
            plt.savefig(output_file)
            print(f"Graph image saved to {output_file}")

    elif command == 'search':
        # We can search by word or topic
        if '-w' in argv:
            w_idx = argv.index('-w') + 1
            word = argv[w_idx]
            with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
                xstr = f.read()
            snet = SocialNetwork()
            snet.build_from_xml(xstr)
            results = snet.search_posts_word(word)
            if results:
                for (uid, uname, body) in results:
                    print(f"User {uid} ({uname}) => {body[:60]}...")
            else:
                print("No posts found with that word.")
        elif '-t' in argv:
            t_idx = argv.index('-t') + 1
            topic = argv[t_idx]
            with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
                xstr = f.read()
            snet = SocialNetwork()
            snet.build_from_xml(xstr)
            results = snet.search_posts_topic(topic)
            if results:
                for (uid, uname, body) in results:
                    print(f"User {uid} ({uname}) => {body[:60]}...")
            else:
                print("No posts found for that topic.")
        else:
            print("Usage: xml_editor search -w <word> -i file.xml OR -t <topic> -i file.xml")

    elif command == 'most_active':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xstr = f.read()
        snet = SocialNetwork()
        snet.build_from_xml(xstr)
        uid, uname, outdeg = snet.find_most_active()
        if uid:
            print(f"Most active user: ID={uid}, Name={uname}, Follows={outdeg}")
        else:
            print("No data found or no users in XML.")

    elif command == 'most_influencer':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xstr = f.read()
        snet = SocialNetwork()
        snet.build_from_xml(xstr)
        uid, uname, count = snet.find_most_influencer()
        if uid:
            print(f"Most influencer: ID={uid}, Name={uname}, Followers={count}")
        else:
            print("No data found or no users in XML.")

    elif command == 'mutual':
        if '-ids' not in argv:
            print("Usage: xml_editor mutual -i file.xml -ids 1,2,3")
            sys.exit(1)
        ids_idx = argv.index('-ids') + 1
        id_list_str = argv[ids_idx]
        user_ids = id_list_str.split(',')
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xstr = f.read()
        snet = SocialNetwork()
        snet.build_from_xml(xstr)
        mutuals = snet.mutual_followers(user_ids)
        print(f"Users who follow all of {user_ids}: {mutuals}")

    elif command == 'suggest':
        if '-id' not in argv:
            print("Usage: xml_editor suggest -i file.xml -id <user_id>")
            sys.exit(1)
        user_id = argv[argv.index('-id') + 1]
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            xstr = f.read()
        snet = SocialNetwork()
        snet.build_from_xml(xstr)
        suggestions = snet.suggest_follows(user_id)
        if suggestions:
            print(f"Suggested users for {user_id} to follow: {suggestions}")
        else:
            print(f"No suggestions for user {user_id}, or user not found.")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


###############################################################################
# 9) Graphical User Interface (Tkinter)
###############################################################################

class XmlEditorGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("XML Editor - Course Project")

        # File selection area
        file_frame = tk.Frame(self.master)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(file_frame, text="XML File:").pack(side=tk.LEFT)
        self.file_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.file_var, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT)

        # Buttons for basic operations
        btn_frame = tk.Frame(self.master)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(btn_frame, text="Verify (Fix)", command=self.gui_verify).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Format", command=self.gui_format).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="To JSON", command=self.gui_json).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Minify", command=self.gui_minify).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Compress", command=self.gui_compress).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Decompress", command=self.gui_decompress).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Draw Graph", command=self.gui_draw).pack(side=tk.LEFT, padx=2)

        # Buttons for network analysis and searching
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

        # Output area to show results
        self.output_area = scrolledtext.ScrolledText(self.master, width=90, height=20)
        self.output_area.pack(padx=5, pady=5)

        # Button to save output
        tk.Button(self.master, text="Save Output", command=self.save_output).pack(pady=5)

    def browse_file(self):
        fname = filedialog.askopenfilename(title="Select XML file")
        if fname:
            self.file_var.set(fname)

    def _read_xml_file(self):
        path = self.file_var.get().strip()
        if not os.path.isfile(path):
            messagebox.showerror("Error", f"File not found: {path}")
            return None
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    def _write_output(self, text):
        self.output_area.delete('1.0', tk.END)
        self.output_area.insert(tk.END, text)

    # GUI handlers:

    def gui_verify(self):
        content = self._read_xml_file()
        if content is None:
            return
        ok, fixed, msg = verify_xml_structure(content, auto_fix=True)
        to_display = msg
        if ok and fixed != content:
            to_display += "\n\n--- Fixed XML ---\n" + fixed
        self._write_output(to_display)

    def gui_format(self):
        content = self._read_xml_file()
        if content is None:
            return
        formatted = format_xml(content)
        self._write_output(formatted)

    def gui_json(self):
        content = self._read_xml_file()
        if content is None:
            return
        jdata = xml_to_json(content)
        if jdata is None:
            self._write_output("Error converting XML to JSON (maybe malformed).")
        else:
            self._write_output(jdata)

    def gui_minify(self):
        content = self._read_xml_file()
        if content is None:
            return
        mini_str = minify_xml(content)
        self._write_output(mini_str)

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
            self._write_output("Output area is empty. Nothing to decompress.")
            return
        import json
        try:
            bundle = json.loads(text)
            comp_data = bundle['compressed']
            merges_map = bundle['merges_map']
            original = decompress_data(comp_data, merges_map)
            self._write_output(original)
        except:
            self._write_output("Could not parse the compressed JSON.")

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
        uid, uname, outdeg = snet.find_most_active()
        if uid:
            self._write_output(f"Most active user: ID={uid}, Name={uname}, Follows={outdeg}")
        else:
            self._write_output("No users found or no data present.")

    def gui_most_influencer(self):
        content = self._read_xml_file()
        if content is None:
            return
        snet = SocialNetwork()
        snet.build_from_xml(content)
        uid, uname, count = snet.find_most_influencer()
        if uid:
            self._write_output(f"Most influencer: ID={uid}, Name={uname}, Followers={count}")
        else:
            self._write_output("No users found or no data present.")

    def gui_mutual(self):
        content = self._read_xml_file()
        if content is None:
            return
        ids_str = self.mutual_var.get().strip()
        if not ids_str:
            self._write_output("No user IDs provided for mutual followers check.")
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
            self._write_output("No user ID provided for suggestion.")
            return
        snet = SocialNetwork()
        snet.build_from_xml(content)
        suggestions = snet.suggest_follows(uid)
        self._write_output(f"Suggestions for user {uid}: {suggestions}")

    def gui_search_word(self):
        content = self._read_xml_file()
        if content is None:
            return
        word = self.word_var.get().strip()
        if not word:
            self._write_output("No word entered.")
            return
        snet = SocialNetwork()
        snet.build_from_xml(content)
        results = snet.search_posts_word(word)
        if not results:
            self._write_output("No posts found containing that word.")
        else:
            display_str = "Posts containing the word:\n"
            for (uid, uname, body) in results:
                display_str += f"User {uid} ({uname}): {body[:70]}...\n"
            self._write_output(display_str)

    def gui_search_topic(self):
        content = self._read_xml_file()
        if content is None:
            return
        topic = self.topic_var.get().strip()
        if not topic:
            self._write_output("No topic entered.")
            return
        snet = SocialNetwork()
        snet.build_from_xml(content)
        results = snet.search_posts_topic(topic)
        if not results:
            self._write_output("No posts found with that topic.")
        else:
            display_str = "Posts containing the topic:\n"
            for (uid, uname, body) in results:
                display_str += f"User {uid} ({uname}): {body[:70]}...\n"
            self._write_output(display_str)

    def save_output(self):
        text = self.output_area.get('1.0', tk.END)
        if not text.strip():
            messagebox.showinfo("Info", "Output area is empty.")
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
    # If a command is given, we assume CLI mode
    if len(sys.argv) > 1:
        cli_main()
    else:
        # Otherwise, launch the GUI
        gui_main()
