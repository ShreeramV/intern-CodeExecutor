
import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import CodeEditor from "./components/CodeEditor";
import GenerateQuestions from "./components/GenerateQuestions";
import QuestionList from "./components/QuestionList";

function App() {
  return (
    <Router>
      <Routes>
        {/* Route to generate questions */}
        <Route path="/qngenerate" element={<GenerateQuestions />} />
        <Route path="/" element={<QuestionList />} />

        {/* Route to code editor with question ID and optional question data via state */}
        <Route path="/code-editor/:id" element={<CodeEditor />} />
      </Routes>
    </Router>
  );
}

export default App;
