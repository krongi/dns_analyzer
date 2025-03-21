import React, { useState, useEffect } from "react";

const App = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('Waiting to start');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [data, setData] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedItems, setExpandedItems] = useState({});

  const API_BASE = "http://10.10.1.26:5000";

  // ✅ Fetch list of processed result filenames ONCE when component mounts
  useEffect(() => {
    fetchResults();
  }, []); // ⬅ Dependency array ensures it runs only once

  // ✅ Fetch filenames from /results (previously processed analyses)
  const fetchResults = async () => {
    try {
        const response = await fetch(`${API_BASE}/results`);
        if (!response.ok) throw new Error("Failed to fetch results");

        const result = await response.json();
        console.log("Fetched filenames:", result.files); // ✅ Debugging Output
        setUploadedFiles(result.files || []);
    } catch (error) {
        console.error("Error fetching results:", error);
    }
};

const handleFileSelection = async (file) => {
    if (!file) return; // Prevent fetching when no file is selected

    setSelectedFile(file);

    try {
        const response = await fetch(`${API_BASE}/processed-results?file=${file}`);
        if (!response.ok) throw new Error("Failed to fetch file contents");

        const jsonData = await response.json();
        setData(jsonData); // ✅ Store the selected file’s JSON for display
        console.log("Fetched data for:", file, jsonData); // Debugging Output
    } catch (error) {
        console.error("Error fetching file contents:", error);
    }
};

const handleFileChange = (event) => {
  const file = event.target.files[0]; // Get the selected file
  if (file) {
      setSelectedFile(file);
      console.log("Selected file:", file.name); // Debugging output
  }
};

  const uploadFile = async () => {
    if (!selectedFile) return alert("Please select a file first.");
  
    const formData = new FormData();
    formData.append("file", selectedFile);
  
    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });
  
      if (!response.ok) throw new Error("Upload failed");
  
      const result = await response.json();
      setUploadMessage(result.message);

      // ✅ Refresh results after upload
      fetchResults();
    } catch (error) {
      setUploadMessage("Upload error: " + error.message);
    }
  };

  const startProcessing = async () => {
    setProcessing(true);
    setProgress(0);
    setCurrentStep('Starting processing...');
  
    try {
      const response = await fetch(`${API_BASE}/start-processing`, {method: "POST" , headers: {'Content-Type': 'application/json',},body: JSON.stringify({trigger: true}),});
      if (!response.ok) throw new Error("Failed to start processing");
    } catch (error) {
      console.error("Error starting processing:", error);
      setProcessing(false);
      return;
    }
  
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE}/progress`);
        if (!response.ok) throw new Error("Failed to fetch progress");
        const result = await response.json();
        setProgress(result.progress || 0);
        setCurrentStep(result.message || 'Processing...');
  
        if (result.progress >= 100) {
          clearInterval(interval);
          fetchResults(); // ✅ Refresh results after processing
          setProcessing(false);
        }
      } catch (error) {
        console.error("Error fetching progress:", error);
        setProgress(0);
        setCurrentStep("Error during processing");
        clearInterval(interval);
        setProcessing(false);
      }
    }, 1000);
  };

  const toggleExpand = (sld) => {
    setExpandedItems((prev) => ({ ...prev, [sld]: !prev[sld] }));
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900 text-gray-300 overflow-hidden">
      <div className="w-full max-w-3xl bg-gray-800 p-6 rounded-lg shadow-lg overflow-y-auto max-h-screen">
        <h1 className="text-3xl font-bold text-center mb-6">DNS Log Analyzer</h1>
        
        <div className="flex flex-col items-center mb-6">
          <select onChange={(e) => handleFileSelection(e.target.value)} className="mb-3 bg-gray-700 text-white px-4 py-2 rounded-lg cursor-pointer shadow-md">
            <option value="">Select a previously processed analysis</option>
            {uploadedFiles.length === 0 && <option disabled>No files available</option>}
            {uploadedFiles.map((file, index) => (
              <option key={index} value={file}>{file}</option>
            ))}
          </select>
        </div>

        <input type="file" onChange={handleFileChange} className="mb-3 bg-gray-700 text-white px-4 py-2 rounded-lg cursor-pointer shadow-md" />
        <button onClick={uploadFile} className="bg-blue-500 text-white px-4 py-2 rounded-lg mr-2">
          Upload
        </button>
        {uploadMessage && <p className="text-center mt-2 text-gray-400">{uploadMessage}</p>}

        <div className="text-center">
          <button onClick={startProcessing} disabled={processing} className="bg-green-500 text-white px-4 py-2 rounded-lg">
            Start Processing
          </button>
        </div>

        <div className="mt-4">
          <p className="text-center mt-2 text-gray-400">{currentStep}</p>
          <div className="bg-gray-700 w-full h-4 rounded-lg overflow-hidden">
            <div className="bg-blue-500 h-full" style={{ width: `${progress}%` }}></div>
          </div>
          <p className="text-center mt-2 text-gray-400">Progress: {progress}%</p>
        </div>

        {data && (
          <div className="mt-6 overflow-y-auto max-h-96">
            <h2 className="text-2xl font-semibold mb-4 text-center">Results</h2>
            {Object.entries(data).map(([sld, details]) => (
              <div key={sld} className="mb-4 bg-gray-700 p-4 rounded-lg">
                <button onClick={() => toggleExpand(sld)} className="text-lg font-semibold text-blue-400 w-full text-left">
                  {expandedItems[sld] ? "▼ " : "▶ "}{sld}
                </button>
                {expandedItems[sld] && (
                  <div className="mt-2">
                    <pre className="text-gray-300 text-sm">
                      {details.whois ? details.whois.slice(0, 10).join("\n") + "..." : "No WHOIS data"}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
