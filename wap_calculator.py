import argparse
import xml.etree.ElementTree as ET


def find_basetime(root, course, gender, stroke):
    """
    Finds the base time for a given event by searching the XML data.

    Args:
        root: The root element of the parsed XML tree.
        course (str): The course length ('SCM' or 'LCM').
        gender (str): The gender ('Men', 'Women', or 'Mixed').
        stroke (str): The name of the swimming event.

    Returns:
        float: The base time in seconds, or None if not found.
    """
    query = (f"./course[@type='{course.upper()}']/"
             f"gender[@name='{gender.capitalize()}']/"
             f"event[stroke='{stroke}']")

    event_node = root.find(query)

    if event_node is not None:
        basetime_node = event_node.find('basetime_seconds')
        if basetime_node is not None:
            return float(basetime_node.text)

    return None


def calculate_points(basetime, input_time):
    """
    Calculates the World Aquatics points using the specified formula.

    Formula: 1000 * (basetime / input_time)^3

    Args:
        basetime (float): The base time for the event.
        input_time (float): The swimmer's time for the event.

    Returns:
        float: The calculated points. Returns 0 if input_time is not positive.
    """
    if input_time <= 0:
        return 0.0

    points = 1000 * (basetime / input_time) ** 3
    return points


def format_time(seconds):
    """
    Converts a time in total seconds to a mm:ss.tt formatted string.
    """
    if seconds < 0:
        return "00:00.00"
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:05.2f}"


def main():
    """
    Main function to parse arguments and calculate points.
    """
    parser = argparse.ArgumentParser(
        description="Calculate World Aquatics points for a swimming performance.",
        epilog="Example: python calculate_points.py --course SCM --gender Men --stroke \"50m Freestyle\" --time 20.16"
    )

    parser.add_argument("--course", choices=['SCM', 'LCM'], required=True,
                        help="Course length: SCM (25m) or LCM (50m).")
    parser.add_argument("--gender", choices=['Uomini', 'Donne', 'Mixed'], required=True,
                        help="Gender category for the event.")
    parser.add_argument("--stroke", type=str, required=True, help="The swimming event, e.g., '100m Freestyle'.")
    parser.add_argument("--time", type=float, required=True, help="The achieved time in seconds.")

    args = parser.parse_args()

    tree = ET.parse('data/basetime.xml')
    root = tree.getroot()

    basetime = find_basetime(root, args.course, args.gender, args.stroke)

    if basetime is None:
        print(f"Error: Could not find a base time for the specified event.")
        print(f"  Course: {args.course}, Gender: {args.gender}, Stroke: '{args.stroke}'")
        return

    # Calculate the points
    points = calculate_points(basetime, args.time)

    # Print the results
    print("\n--- World Aquatics Points Calculation ---")
    print(f"  Event          : {args.stroke}")
    print(f"  Course         : {args.course}")
    print(f"  Gender         : {args.gender}")
    print(f"  Input Time (s) : {args.time:.2f}")
    print(f"  Base Time (s)  : {basetime:.2f}")
    print("-----------------------------------------")
    print(f"  Calculated Points: {points:.2f} 🏊")
    print("-----------------------------------------")


if __name__ == "__main__":
    main()