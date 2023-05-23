# Author: Lickos A.

import requests
import yaml
import json


def download_yaml_data(url):
    # Include the User-Agent header
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Send GET request with headers
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.text
        #print(data)

        return data

    except requests.RequestException as e:
        print(f"Error retrieving data: {e}")
        return None


def extract_traffic_volume(traffic_data):
    # Extract the traffic volume data from the YAML
    volume_dns_udp_queries_received_ipv4 = traffic_data.get("dns-udp-queries-received-ipv4")
    volume_dns_udp_queries_received_ipv6 = traffic_data.get("dns-udp-queries-received-ipv6")
    volume_dns_tcp_queries_received_ipv6 = traffic_data.get("dns-tcp-queries-received-ipv6")
    volume_dns_tcp_queries_received_ipv4 = traffic_data.get("dns-tcp-queries-received-ipv4")
    volume_dns_udp_responses_sent_ipv4 = traffic_data.get("dns-udp-responses-sent-ipv4")
    volume_dns_udp_responses_sent_ipv6 = traffic_data.get("dns-udp-responses-sent-ipv6")
    volume_dns_tcp_responses_sent_ipv6 = traffic_data.get("dns-tcp-responses-sent-ipv6")
    volume_dns_tcp_responses_sent_ipv4 = traffic_data.get("dns-tcp-responses-sent-ipv4")

    volume = {
        "dns-udp-queries-received-ipv4": volume_dns_udp_queries_received_ipv4,
        "dns-udp-queries-received-ipv6": volume_dns_udp_queries_received_ipv6,
        "dns-tcp-queries-received-ipv6": volume_dns_tcp_queries_received_ipv6,
        "dns-tcp-queries-received-ipv4": volume_dns_tcp_queries_received_ipv4,
        "dns-udp-responses-sent-ipv4": volume_dns_udp_responses_sent_ipv4,
        "dns-udp-responses-sent-ipv6": volume_dns_udp_responses_sent_ipv6,
        "dns-tcp-responses-sent-ipv6": volume_dns_tcp_responses_sent_ipv6,
        "dns-tcp-responses-sent-ipv4": volume_dns_tcp_responses_sent_ipv4
    }

    return volume


def get_traffic_volume(link, typeOps, date):
    url = f"{link}/{date[:4]}/{date[4:6]}/traffic-volume/{typeOps}-root-{date}-traffic-volume.yaml"
    #print(url)
    if link == "https://www.disa.mil/G-Root/G-Root-Stats":
        return retrieve_data(link, typeOps, date)

    try:
        # Download YAML data using the updated function
        data = download_yaml_data(url)
        # Parse the YAML data
        traffic_data = yaml.safe_load(data)

        # Extract the traffic volume
        volume = extract_traffic_volume(traffic_data)

        return volume

    except requests.RequestException as e:
        print(f"Error retrieving data: {e}")
        return None


def retrieve_data(link, traffic_type,date):
    full_path = f"{date[:4]}/{date[4:6]}/traffic-volume/{traffic_type}-root-{date}-traffic-volume.yaml"
    payload = {
        "scController": "Display",
        "scAction": "ReadText",
        "FullPath": full_path
    }
    print(full_path)

    try:
        # Send POST request to retrieve data
        response = requests.post(link, data=payload)
        if response.status_code == 200:
            response.raise_for_status()
            data = response.text

            # Extract the traffic volume
            traffic_data = yaml.safe_load(data)
            volume = extract_traffic_volume(traffic_data)

            return volume
        else:
            print(f"Error retrieving data. Status Code: {response.status_code}")
            return None

    except requests.RequestException as e:
        print(f"Error retrieving data: {e}")
        return None


def calculate_total_traffic_volume(operators, date):
    # Dictionary to store the total traffic volume by operators
    total_traffic_volume_by_operators = {}

    # List to store all traffic volumes
    all_traffic_volumes = []

    for operator, info in operators.items():
        volume = get_traffic_volume(info["link"], info["type"], date)
        print(f"Operator: {operator}")
        print(f"Type: {info['type']}")
        print(f"Traffic Volume: {volume}")
        print("-" * 30)

        if volume:
            # Sum the traffic volume
            total_traffic_volume = sum(volume.values())

            # Store the total traffic volume for the operator
            total_traffic_volume_by_operators[operator] = total_traffic_volume

            # Add the traffic volume to the list of all traffic volumes
            all_traffic_volumes.append({operator: volume})

    # Create a JSON object to store the results
    result = {
        "total_traffic_volume_by_operators": total_traffic_volume_by_operators,
        "total_traffic_volume_by_type": {},
        "total_traffic_volume": 0,
        "total_traffic_volume_by_received_sent": {
            "received": 0,
            "sent": 0
        }
    }

    # Get the total sum of traffic volume by traffic type
    for volume_dict in all_traffic_volumes:
        operator = list(volume_dict.keys())[0]
        volume = volume_dict[operator]
        for traffic_type, value in volume.items():
            result["total_traffic_volume_by_type"][traffic_type] = result["total_traffic_volume_by_type"].get(traffic_type, 0) + value

    # Calculate the total traffic volume
    result["total_traffic_volume"] = sum(total_traffic_volume_by_operators.values())

    # Calculate the total sum of traffic volume by received and sent categories
    for volume_dict in all_traffic_volumes:
        operator = list(volume_dict.keys())[0]
        volume = volume_dict[operator]
        for traffic_type, value in volume.items():
            if "received" in traffic_type:
                result["total_traffic_volume_by_received_sent"]["received"] += value
            elif "sent" in traffic_type:
                result["total_traffic_volume_by_received_sent"]["sent"] += value

    # Convert the result to JSON
    json_result = json.dumps(result, indent=4)
    return json_result


def main():
    operators = {
        "Verisign, Inc.": {"link": "https://a.root-servers.org/rssac-metrics/raw", "type": "a"},
        "Information Sciences Institute": {"link": "http://b.root-servers.org/rssac", "type": "b"},
        "Cogent Communications": {"link": "https://c.root-servers.org/rssac002-metrics", "type": "c"},
        "University of Maryland": {"link": "http://www.droot.maxgigapop.net/rssac002", "type": "d"},
        "NASA Ames Research Center": {"link": "https://e.root-servers.org/rssac", "type": "e"},
        "Internet Systems Consortium, Inc.": {"link": "http://rssac-stats.isc.org/rssac002", "type": "f"},
        "Defense Information Systems Agency": {"link": "https://www.disa.mil/G-Root/G-Root-Stats", "type": "g"},
        "U.S. Army DEVCOM Army Research Lab": {"link": "https://h.root-servers.org/rssac002-metrics", "type": "h"},
        "Netnod": {"link": "https://www.netnod.se/rssac002-metrics", "type": "i"},
        "RIPE NCC": {"link": "https://www-static.ripe.net/dynamic/rssac002-metrics", "type": "k"},
        "ICANN": {"link": "https://stats.dns.icann.org/rssac", "type": "l"},
        "WIDE Project": {"link": "https://rssac.wide.ad.jp/rssac002-metrics", "type": "m"}
    }
    date = '20230501'
    r = calculate_total_traffic_volume(operators,date)
    print(r)


if __name__ == "__main__":
    main()
