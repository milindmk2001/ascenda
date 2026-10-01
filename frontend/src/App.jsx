import React, { useState, useEffect } from 'react';
import { getTracks, getGrades, resolveHubSubjects } from './services/api';
import CourseReader from './CourseReader'; // Adjust path if CourseReader is in another folder
import './App.css';

export default function App() {
  const [tracks, setTracks] = useState([]);
  const [selectedTrack, setSelectedTrack] = useState('');
  const [grades, setGrades] = useState([]);
  const [selectedGrade, setSelectedGrade] = useState('');
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeSubject, setActiveSubject] = useState(null);

  // 1. Fetch Dynamic Tracks & Deduplicated Grades from Supabase on mount
  useEffect(() => {
    const fetchFilterOptions = async () => {
      try {
        const [trackList, gradeList] = await Promise.all([
          getTracks(),
          getGrades(),
        ]);

        if (trackList && trackList.length > 0) {
          setTracks(trackList);
          setSelectedTrack(trackList[0]);
        }

        if (gradeList && gradeList.length > 0) {
          setGrades(gradeList);
          setSelectedGrade(gradeList[0].name);
        }
      } catch (err) {
        console.error('Failed to load hub filters:', err);
      }
    };

    fetchFilterOptions();
  }, []);

  // 2. Fetch Course Cards whenever Track or Grade changes
  useEffect(() => {
    if (selectedTrack && selectedGrade) {
      setLoading(true);
      resolveHubSubjects(selectedTrack, selectedGrade)
        .then((data) => {
          setSubjects(data || []);
          setLoading(false);
        })
        .catch((err) => {
          console.error('Error resolving hub subjects:', err);
          setLoading(false);
        });
    }
  }, [selectedTrack, selectedGrade]);

  // Handle course reader navigation
  if (activeSubject) {
    return (
      <CourseReader
        subject={activeSubject}
        subjectId={activeSubject.id}
        onBack={() => setActiveSubject(null)}
      />
    );
  }

  return (
    <div className="app-container">
      {/* HEADER / NAVBAR */}
      <header className="navbar">
        <div className="brand-logo">
          <span className="dot"></span> ASCENDA LEARNING PLATFORM
        </div>
        <nav className="nav-links">
          <button className="nav-btn active">CURRICULUM HUB</button>
        </nav>
      </header>

      {/* MAIN HUB AREA */}
      <main className="hub-body">
        <div className="hub-header">
          <div>
            <h2>CURRICULUM INDEX</h2>
            <p className="subtitle">
              Select a target exam track and grade level to browse available subjects.
            </p>
          </div>

          {/* DYNAMIC DROPDOWNS */}
          <div className="dropdown-group">
            <select
              value={selectedTrack}
              onChange={(e) => setSelectedTrack(e.target.value)}
              className="select-input"
            >
              {tracks.map((track) => (
                <option key={track} value={track}>
                  {track}
                </option>
              ))}
            </select>

            <select
              value={selectedGrade}
              onChange={(e) => setSelectedGrade(e.target.value)}
              className="select-input"
            >
              {grades.map((grade) => (
                <option key={grade.id} value={grade.name}>
                  {grade.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* SUBJECT CARDS DISPLAY */}
        <div className="cards-grid">
          {loading ? (
            <p className="status-text">Loading curriculum...</p>
          ) : subjects.length > 0 ? (
            subjects.map((subject) => (
              <div
                key={subject.id}
                className="subject-card"
                onClick={() => setActiveSubject(subject)}
                style={{ cursor: 'pointer' }}
              >
                <span className="badge">{subject.discipline || 'CORE MODULE'}</span>
                <h3>{subject.title || subject.subject_name}</h3>
                <button
                  className="card-action"
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveSubject(subject);
                  }}
                >
                  Launch Reader &rarr;
                </button>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <p>NO ACTIVE MODULES FOUND</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}