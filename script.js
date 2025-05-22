document.addEventListener('DOMContentLoaded', function () {
    // Category Breakdown by Split
    const categoryData = {
        train: {
            description: 49241,
            action: 37006,
            count: 33276,
            temporal: 32855,
            location: 14907,
            'relative-position': 9826
        },
        val: {
            description: 6182,
            action: 4938,
            count: 3953,
            temporal: 3915,
            location: 1977,
            'relative-position': 1298
        },
        test: {
            description: 7243,
            action: 5745,
            count: 4668,
            temporal: 4589,
            location: 2361,
            'relative-position': 1476
        }
    };

    const categories = Object.keys(categoryData.train);
    const customColors = ['#4c72b0', '#dd8452', '#55a868', '#c44e52', '#8172b3', '#937860', '#da8bc3', '#8c8c8c', '#ccb974', '#64b5cd'];

    const traces = ['train', 'val', 'test'].map((split, i) => ({
        name: split,
        x: categories,
        y: categories.map(cat => categoryData[split][cat]),
        type: 'bar',
        marker: {
            color: customColors[i]
        }
    }));

    Plotly.newPlot('categoryBreakdownPlot', traces, {
        title: 'Category Breakdown by Split',
        barmode: 'group',
        xaxis: { title: 'Category' },
        yaxis: { title: 'Count' },
        height: 450,
        responsive: true,
        autosize: true,
        margin: { t: 60, b: 100, l: 80, r: 60 }
    });

    // Modality Breakdown by Split
    const modalityData = {
        train: {
            visual: 101551,
            'audio-visual': 39545,
            audio: 36031
        },
        val: {
            visual: 13356,
            'audio-visual': 4684,
            audio: 4221
        },
        test: {
            visual: 15719,
            'audio-visual': 5429,
            audio: 4937
        }
    };

    const modalities = Object.keys(modalityData.train);
    const modalityTraces = ['train', 'val', 'test'].map((split, i) => ({
        name: split,
        x: modalities,
        y: modalities.map(mod => modalityData[split][mod]),
        type: 'bar',
        marker: {
            color: customColors[i]
        }
    }));

    Plotly.newPlot('modalityBreakdownPlot', modalityTraces, {
        title: 'Modality Breakdown by Split',
        barmode: 'group',
        xaxis: { title: 'Modality' },
        yaxis: { title: 'Count' },
        height: 450,
        responsive: true,
        autosize: true,
        margin: { t: 60, b: 100, l: 80, r: 60 }
    });

    // Modality-Category Heatmap
    const modalityCategoryData = {
        visual: {
            description: 32050,
            count: 27995,
            action: 20056,
            temporal: 18785,
            location: 19146,
            'relative-position': 12593
        },
        audio: {
            description: 25471,
            count: 11696,
            temporal: 7393,
            action: 558,
            location: 43,
            'relative-position': 2
        },
        'audio-visual': {
            temporal: 15159,
            action: 27075,
            description: 5145,
            count: 2206,
            location: 56,
            'relative-position': 5
        }
    };

    const heatmapCategories = ['description', 'count', 'action', 'temporal', 'location', 'relative-position'];
    const heatmapModalities = ['visual', 'audio', 'audio-visual'];

    const heatmapData = [{
        z: heatmapModalities.map(mod => heatmapCategories.map(cat => modalityCategoryData[mod][cat] || 0)),
        x: heatmapCategories,
        y: heatmapModalities,
        type: 'heatmap',
        colorscale: [
            [0, '#e6f3ff'],    // Very light blue
            [0.2, '#b3d9ff'],  // Light blue
            [0.4, '#80bfff'],  // Medium light blue
            [0.6, '#4da6ff'],  // Medium blue
            [0.8, '#1a8cff'],  // Dark blue
            [1, '#0066cc']     // Very dark blue
        ],
        showscale: true,
        colorbar: {
            title: 'Count'
        },
        text: heatmapModalities.map(mod => heatmapCategories.map(cat => modalityCategoryData[mod][cat] || 0)),
        texttemplate: '%{text:,}',
        textfont: {
            size: 12
        },
        hoverongaps: false,
        hoverinfo: 'text',
        textposition: 'middle center'
    }];

    const heatmapLayout = {
        title: 'Modality-Category Distribution',
        xaxis: {
            title: 'Category',
            tickangle: -45
        },
        yaxis: {
            title: 'Modality'
        },
        height: 450,
        responsive: true,
        autosize: true,
        margin: { t: 60, b: 100, l: 100, r: 60 },
        annotations: heatmapModalities.flatMap((mod, i) =>
            heatmapCategories.map((cat, j) => {
                const value = modalityCategoryData[mod][cat];
                return {
                    x: cat,
                    y: mod,
                    text: value.toLocaleString(),
                    showarrow: false,
                    font: {
                        color: value > 15000 ? 'white' : 'black',
                        size: 12
                    }
                };
            })
        )
    };

    Plotly.newPlot('modalityCategoryHeatmap', heatmapData, heatmapLayout);

    // Questions per Video Distribution
    const questionsPerVideoData = {
        "0": 1,
        "1": 23,
        "2": 797,
        "3": 1016,
        "4": 42,
        "5": 3963,
        "6": 1113,
        "7": 8772,
        "8": 3517,
        "9": 2317,
        "10": 2482,
        "11": 189,
        "12": 3423,
        "13": 1128,
        "14": 65,
        "15": 13,
        "16": 2
    };

    const questionsPerVideoTrace = {
        x: Object.keys(questionsPerVideoData),
        y: Object.values(questionsPerVideoData),
        type: 'bar',
        marker: {
            color: customColors[0]
        }
    };

    Plotly.newPlot('questionsPerVideoPlot', [questionsPerVideoTrace], {
        title: 'Questions per Video Distribution',
        xaxis: {
            title: 'Number of Questions per Video',
            range: [0, 16]
        },
        yaxis: { title: 'Number of Videos' },
        height: 450,
        responsive: true,
        autosize: true,
        margin: { t: 60, b: 100, l: 80, r: 60 }
    });

    // Question Length Distribution
    const questionLengthData = {
        "2": 2,
        "3": 20,
        "4": 119,
        "5": 1664,
        "6": 4796,
        "7": 22199,
        "8": 44246,
        "9": 38099,
        "10": 35744,
        "11": 28268,
        "12": 20511,
        "13": 10586,
        "14": 7159,
        "15": 4712,
        "16": 2811,
        "17": 1652,
        "18": 1085,
        "19": 866,
        "20": 367,
        "21": 223,
        "22": 134,
        "23": 109,
        "24": 48,
        "25": 39,
        "26": 17,
        "27": 10,
        "28": 4,
        "29": 3,
        "31": 2
    };

    const questionLengthTrace = {
        x: Object.keys(questionLengthData),
        y: Object.values(questionLengthData),
        type: 'bar',
        marker: {
            color: customColors[1]
        }
    };

    Plotly.newPlot('questionLengthPlot', [questionLengthTrace], {
        title: 'Question Length Distribution',
        xaxis: {
            title: 'Question Length (words)',
            range: [2, 31]
        },
        yaxis: { title: 'Number of Questions' },
        height: 450,
        responsive: true,
        autosize: true,
        margin: { t: 60, b: 100, l: 80, r: 60 }
    });

    // Top 20 Correct Options
    const correctOptionsData = {
        'Two': 10540,
        'Music': 5588,
        'Three': 5156,
        'Four': 3770,
        'Twice': 3335,
        'One': 3022,
        'Once': 2956,
        'Red': 2386,
        'Blue': 1913,
        'Three times': 1596,
        'White': 1428,
        'Five': 1368,
        'Four times': 1302,
        'Black': 1250,
        'Male speech': 1203,
        'Yellow': 1187,
        'Speech': 1141,
        'Green': 1129,
        'To the left': 1087,
        'Singing': 962
    };

    const correctOptionsTrace = {
        x: Object.keys(correctOptionsData),
        y: Object.values(correctOptionsData),
        type: 'bar',
        marker: {
            color: customColors[2]
        }
    };

    Plotly.newPlot('correctOptionsPlot', [correctOptionsTrace], {
        title: 'Top 20 Most Frequent Correct Answer Options',
        xaxis: { title: 'Answer Option' },
        yaxis: { title: 'Frequency' },
        height: 450,
        responsive: true,
        autosize: true,
        margin: { t: 60, b: 150, l: 80, r: 60 }
    });

    // Top 20 Non-stopwords
    const nonStopwordsData = {
        'video': 114802,
        'sound': 64825,
        'man': 37783,
        'heard': 33978,
        'accompanies': 21770,
        'visible': 17348,
        'located': 17095,
        'movement': 16774,
        'happens': 16635,
        'times': 14378,
        'doing': 14274,
        'color': 13704,
        's': 13309,
        'does': 12952,
        'background': 11671,
        'relative': 10662,
        'woman': 10187,
        'position': 10181,
        'event': 8664,
        'person': 8174
    };

    const nonStopwordsTrace = {
        x: Object.keys(nonStopwordsData),
        y: Object.values(nonStopwordsData),
        type: 'bar',
        marker: {
            color: customColors[3]
        }
    };

    Plotly.newPlot('nonStopwordsPlot', [nonStopwordsTrace], {
        title: 'Top 20 Most Frequent Non-stopwords in Questions',
        xaxis: { title: 'Word' },
        yaxis: { title: 'Frequency' },
        height: 450,
        responsive: true,
        autosize: true,
        margin: { t: 60, b: 150, l: 80, r: 60 }
    });

    // Add window resize handler
    window.addEventListener('resize', function () {
        const plotIds = [
            'categoryBreakdownPlot',
            'modalityBreakdownPlot',
            'modalityCategoryHeatmap',
            'questionsPerVideoPlot',
            'questionLengthPlot',
            'correctOptionsPlot',
            'nonStopwordsPlot'
        ];

        plotIds.forEach(id => {
            Plotly.relayout(id, {
                'width': document.getElementById(id).offsetWidth
            });
        });
    });

    // Interactive Visualizations
    const interactiveVizSection = document.querySelector('h3:contains("Interactive Visualizations")');
    if (interactiveVizSection) {
        interactiveVizSection.insertAdjacentHTML('beforebegin', `
            <h3 class="text-xl font-semibold mb-4">Interactive Visualizations</h3>
        `);
    }
});
