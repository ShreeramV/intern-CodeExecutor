

// import React, { useState } from 'react';
// import axios from 'axios';
// import { useNavigate } from 'react-router-dom';
// import './GenerateQuestions.css';

// const GenerateQuestions = () => {
//   const [topic, setTopic] = useState('');
//   const [difficulty, setDifficulty] = useState('Easy');
//   const [questions, setQuestions] = useState([]);
//   const navigate = useNavigate();

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     try {
//       const res = await axios.post('http://localhost:8000/api/generate_questions/', {
//         topic,
//         difficulty,
//       });
//       setQuestions(res.data.generated_questions);
//     } catch (err) {
//       console.error('Failed to generate questions:', err);
//     }
//   };

//   const handleSelectQuestion = (question) => {
//     navigate(`/code-editor/${question.id}`, { state: { question } });
//   };

//   return (
//     <>
//       <div className="generate-header">
//         <h2>Generate Coding Questions</h2>
//         <form className="generate-form" onSubmit={handleSubmit}>
//           <input
//             type="text"
//             placeholder="Enter topic"
//             value={topic}
//             onChange={(e) => setTopic(e.target.value)}
//             required
//           />
//           <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
//             <option value="Easy">Easy</option>
//             <option value="Medium">Medium</option>
//             <option value="Hard">Hard</option>
//           </select>
//           <button type="submit">Generate</button>
//         </form>
//       </div>

//       <div className="generate-container">
//         <div className="question-list">
//           {questions.map((q) => (
//             <div
//               key={q.id}
//               className="question-card"
//               onClick={() => handleSelectQuestion(q)} // <-- Pass full question object
//             >
//               <h4>{q.title}</h4>
//               <p>{q.description}</p>
//             </div>
//           ))}
//         </div>
//       </div>
//     </>
//   );
// };

// export default GenerateQuestions;




import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './GenerateQuestions.css';

const GenerateQuestions = () => {
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('Easy');
  const [questions, setQuestions] = useState(() => {
    const saved = localStorage.getItem('generatedQuestions');
    return saved ? JSON.parse(saved) : [];
  });

  const navigate = useNavigate();

  useEffect(() => {
    // Clear localStorage only when user closes or refreshes the tab
    window.addEventListener('beforeunload', () => {
      localStorage.removeItem('generatedQuestions');
    });

    return () => {
      window.removeEventListener('beforeunload', () => {
        localStorage.removeItem('generatedQuestions');
      });
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:8000/api/generate_questions/', {
        topic,
        difficulty,
      });
      setQuestions(res.data.generated_questions);
      localStorage.setItem('generatedQuestions', JSON.stringify(res.data.generated_questions));
    } catch (err) {
      console.error('Failed to generate questions:', err);
    }
  };

  const handleSelectQuestion = (question) => {
    navigate(`/code-editor/${question.id}`, { state: { question } });
  };

  return (
    <>
      <div className="generate-header">
        <h2>Generate Coding Questions</h2>
        <form className="generate-form" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Enter topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            required
          />
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            <option value="Easy">Easy</option>
            <option value="Medium">Medium</option>
            <option value="Hard">Hard</option>
          </select>
          <button type="submit">Generate</button>
        </form>
      </div>

      <div className="generate-container">
        <div className="question-list">
          {questions.map((q) => (
            <div
              key={q.id}
              className="question-card"
              onClick={() => handleSelectQuestion(q)}
            >
              <h4>{q.title}</h4>
              <p>{q.description}</p>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

export default GenerateQuestions;
