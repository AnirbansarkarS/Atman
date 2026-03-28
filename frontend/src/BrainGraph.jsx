import React, { useState, useEffect } from 'react';

const BrainGraph = () => {
    const [graphUrl, setGraphUrl] = useState('');

    useEffect(() => {
        // Fetch graph from backend API
        fetch('/api/brain-graph')
            .then(response => response.blob())
            .then(imageBlob => {
                const imageUrl = URL.createObjectURL(imageBlob);
                setGraphUrl(imageUrl);
            });
    }, []);

    return (
        <div>
            <h2>Brain Graph</h2>
            {graphUrl ? <img src={graphUrl} alt="Brain Graph" /> : <p>Loading graph...</p>}
        </div>
    );
};

export default BrainGraph;
