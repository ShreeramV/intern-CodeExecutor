

// import React, { useState, useEffect } from 'react';
// import { Link } from 'react-router-dom';
// import './QuestionList.css'; // Import the CSS file

// const QuestionList = () => {
//     const [questions, setQuestions] = useState([]);

//     useEffect(() => {
//         const fetchQuestions = async () => {
//             const response = await fetch('http://localhost:8000/api/questions/');
//             const data = await response.json();
//             setQuestions(data);
//         };

//         fetchQuestions();
//     }, []);

//     return (
//         <div className="question-list-container">
//             <h2 className="question-list-header">Question List</h2>
//             <ul className="question-list">
//                 {questions.map((question) => (
//                     <li key={question.id} className="question-item">
//                         <Link to={`/code-editor/${question.id}`} className="question-link">
//                             <h3 className="question-title">{question.title}</h3>
//                         </Link>
//                         <p className="question-difficulty">
//                             <strong>Difficulty:</strong> {question.difficulty}
//                         </p>
//                     </li>
//                 ))}
//             </ul>
//         </div>
//     );
// };

// export default QuestionList;



import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './QuestionList.css';

const QuestionList = () => {
    const [questions, setQuestions] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchQuestions = async () => {
            const response = await fetch('http://localhost:8000/api/questions/');
            const data = await response.json();
            setQuestions(data);
        };

        fetchQuestions();
    }, []);

    const handleGenerateClick = () => {
        navigate('/qngenerate');
    };

    return (
        <div className="question-list-container">
            <div className="question-list-header">
                <h2>Question List</h2>
                <button onClick={handleGenerateClick} className="generate-button">
                    ➕ Generate Questions
                </button>
            </div>
            <ul className="question-list">
                {questions.map((question) => (
                    <li key={question.id} className="question-item">
                        <Link to={`/code-editor/${question.id}`} className="question-link">
                            <h3 className="question-title">{question.title}</h3>
                        </Link>
                        <p className="question-difficulty">
                            <strong>Difficulty:</strong> {question.difficulty}
                        </p>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default QuestionList;
