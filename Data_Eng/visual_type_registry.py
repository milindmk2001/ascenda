# visual_type_registry.py
VISUAL_TYPES = {
    "number_sequence": {
        "description": "Arithmetic or geometric number sequence with arrows",
        "requiredFields": ["sequence", "rule", "ruleType"],
        "optionalFields": ["showQuestionMark", "highlightLast", "colorScheme"],
        "chapters": ["Ch01", "Ch03"],
        "builder": "build_number_sequence_svg"
    },
    "number_line": {
        "description": "Number line with marked points and direction arrows",
        "requiredFields": ["start", "end", "marked"],
        "chapters": ["Ch06", "Ch10"],
        "builder": "build_number_line_svg"
    },
    "fraction_strip": {
        "description": "Fraction comparison strips side by side",
        "requiredFields": ["fractions"],
        "chapters": ["Ch07"],
        "builder": "build_fraction_strip_svg"
    },
    "geometry_construct": {
        "description": "Lines, angles, and geometric shapes with labels",
        "requiredFields": ["shapes", "labels"],
        "chapters": ["Ch02", "Ch08"],
        "builder": "build_geometry_svg"
    },
    "data_bar_chart": {
        "description": "Vertical bar chart with labelled axes",
        "requiredFields": ["labels", "values", "xLabel", "yLabel"],
        "chapters": ["Ch04"],
        "builder": "build_bar_chart_svg"
    },
    "symmetry_grid": {
        "description": "Grid showing line of symmetry with reflected shapes",
        "requiredFields": ["shape", "axisType"],
        "chapters": ["Ch09"],
        "builder": "build_symmetry_svg"
    },
    "area_grid": {
        "description": "Grid showing area and perimeter of shapes",
        "requiredFields": ["width", "height", "shapeType"],
        "chapters": ["Ch06"],
        "builder": "build_area_grid_svg"
    },
    "factor_tree": {
        "description": "Factor tree showing prime factorisation",
        "requiredFields": ["number", "factors"],
        "chapters": ["Ch05"],
        "builder": "build_factor_tree_svg"
    }
}