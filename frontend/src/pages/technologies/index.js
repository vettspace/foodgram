import { Title, Container, Main } from '../../components';
import styles from './styles.module.css';
import MetaTags from 'react-meta-tags';

const Technologies = () => {
  return (
    <Main>
      <MetaTags>
        <title>О проекте - Технологии</title>
        <meta name="description" content="Узнайте о технологиях, используемых в проекте Фудграм, включая Python, Django и другие." />
        <meta property="og:title" content="О проекте - Технологии" />
        <meta property="og:description" content="Подробная информация о технологиях, применяемых в проекте Фудграм." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://yourwebsite.com/technologies" />
        <meta property="og:image" content="https://yourwebsite.com/images/technologies.jpg" />
      </MetaTags>

      <Container>
        <h1 className={styles.title}>Технологии</h1>
        <div className={styles.content}>
          <div>
            <h2 className={styles.subtitle}>Технологии, которые применены в этом проекте:</h2>
            <div className={styles.text}>
              <ul className={styles.textItem}>
                <li className={styles.textItem}>
                  <strong>Python</strong> - высокоуровневый язык программирования, известный своей простотой и читаемостью. Используется для создания серверной логики.
                </li>
                <li className={styles.textItem}>
                  <strong>Django</strong> - мощный веб-фреймворк для Python, который упрощает создание сложных веб-приложений благодаря встроенным инструментам и библиотекам.
                </li>
                <li className={styles.textItem}>
                  <strong>Django REST Framework</strong> - расширение для Django, которое позволяет легко создавать RESTful API, обеспечивая гибкость и масштабируемость.
                </li>
                <li className={styles.textItem}>
                  <strong>Djoser</strong> - библиотека для Django, которая упрощает управление аутентификацией и авторизацией пользователей через REST API.
                </li>
              </ul>
            </div>
            <div className={styles.additionalInfo}>
              <h3 className={styles.subtitle}>Преимущества использования этих технологий:</h3>
              <ul className={styles.textItem}>
                <li className={styles.textItem}>
                  <strong>Быстрая разработка:</strong> Благодаря Django и его инструментам, разработка веб-приложений становится более быстрой и эффективной.
                </li>
                <li className={styles.textItem}>
                  <strong>Масштабируемость:</strong> Эти технологии позволяют легко масштабировать приложение по мере роста нагрузки.
                </li>
                <li className={styles.textItem}>
                  <strong>Сообщество и поддержка:</strong> Большое сообщество разработчиков, готовых помочь и поделиться опытом.
                </li>
              </ul>
            </div>
            <div className={styles.examples}>
              <h3 className={styles.subtitle}>Примеры использования:</h3>
              <p className={styles.text}>
                Эти технологии используются в различных проектах, от небольших стартапов до крупных корпоративных приложений. Например, Instagram использует Django для своей серверной части.
              </p>
            </div>
          </div>
        </div>
      </Container>
    </Main>
  );
}

export default Technologies;