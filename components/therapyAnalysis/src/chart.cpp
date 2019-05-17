#include "chart.h"
#include <QtGui/QResizeEvent>
#include <QtWidgets/QGraphicsScene>
#include <QtCharts/QChart>
#include <QtCharts/QLineSeries>
#include <QtCharts/QSplineSeries>
#include <QtWidgets/QGraphicsTextItem>


Chart::Chart(QWidget *parent) : QGraphicsView(new QGraphicsScene, parent),
      m_coordX(0), m_coordY(0), m_chart(0)
{
    QVBoxLayout *layout = new QVBoxLayout();
    parent->setLayout(layout);
    layout->addWidget(this);
    QGroupBox *m_legend = new QGroupBox("Series");
    m_groupBox = new QHBoxLayout();
    m_legend->setLayout(m_groupBox);
    layout->addWidget(m_legend);

    setDragMode(QGraphicsView::NoDrag);
    setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    
    // chart
    m_chart = new QChart;
    m_chart->setMinimumSize(640, 480);
    m_chart->legend();

    setRenderHint(QPainter::Antialiasing);
    scene()->addItem(m_chart);

    m_coordX = new QGraphicsSimpleTextItem(m_chart);
    m_coordX->setPos(m_chart->size().width()/2 - 50, m_chart->size().height());
    m_coordX->setText("X: ");
    m_coordY = new QGraphicsSimpleTextItem(m_chart);
    m_coordY->setPos(m_chart->size().width()/2 + 50, m_chart->size().height());
    m_coordY->setText("Y: ");


    this->setMouseTracking(true);
}


void Chart::loadData(std::map<std::string,std::vector<float>> currentMetrics)
{
    //Create series
    std::map<std::string, QLineSeries*> series;
    for(auto const& element: currentMetrics)
    {
        if (element.first != "Time")
        {
            series[element.first] = new QLineSeries();
            series[element.first]->setName(QString::fromStdString(element.first));
        }
    }
    //load data
    for (unsigned int i=0; i<currentMetrics["Time"].size(); i++)
        for(auto const& serie: series)
            serie.second->append(currentMetrics["Time"][i], currentMetrics[serie.first][i]);

    //load graphic and connect signals
    for(auto const& serie: series)
    {
        m_chart->addSeries(serie.second);
        connect(serie.second, &QLineSeries::clicked, this, &Chart::keepCallout);
        connect(serie.second, &QLineSeries::hovered, this, &Chart::tooltip);
        QCheckBox *check = new QCheckBox(QString::fromStdString(serie.first));
        check->setChecked(true);
        connect(check, &QCheckBox::toggled, serie.second, &QSplineSeries::setVisible);
        m_groupBox->addWidget(check);
    }
    m_chart->createDefaultAxes();
    m_chart->setAcceptHoverEvents(true);

    time = (currentMetrics["Time"][currentMetrics["Time"].size()-1]-currentMetrics["Time"][0]);
}
void Chart::saveChart(QString filename)
{
    QPixmap p = this->grab();
    QOpenGLWidget *glWidget  = this->findChild<QOpenGLWidget*>();
    if(glWidget){
        QPainter painter(&p);
        QPoint d = glWidget->mapToGlobal(QPoint()) - this->mapToGlobal(QPoint());
        painter.setCompositionMode(QPainter::CompositionMode_SourceAtop);
        painter.drawImage(d, glWidget->grabFramebuffer());
        painter.end();
    }
    p.save(filename+".png", "PNG");
    //pdf
    QPdfWriter pdfWriter(filename+".pdf");
    pdfWriter.setPageSize(QPageSize(QPageSize::A4));
    pdfWriter.setPageMargins(QMargins(30, 30, 30, 30));
    
    QPainter painter(&pdfWriter);
    painter.setPen(Qt::black);
    painter.setFont(QFont("Times", 12));
    QRect r = painter.viewport();
  //  QTextDocument td;
  //  td.setHtml("<sub>max</sub>=K<sub>2</sub> &middot; 3");
  //  td.drawContents(&painter);
    painter.drawText(r, Qt::AlignLeft, "Fecha informe " + QTime::currentTime().toString()  );
    painter.drawText(r, Qt::AlignLeft, "Tiempo de sesion " + QString::number(time) + " segundos" );
    
    painter.drawPixmap(30,350,7000,7000,p);
    painter.end();    

}


void Chart::resizeEvent(QResizeEvent *event)
{
    if (scene()) {
        scene()->setSceneRect(QRect(QPoint(0, 0), event->size()));
         m_chart->resize(event->size());
         m_coordX->setPos(m_chart->size().width()/2 - 50, m_chart->size().height() - 20);
         m_coordY->setPos(m_chart->size().width()/2 + 50, m_chart->size().height() - 20);
         const auto callouts = m_callouts;
         for (Callout *callout : callouts)
             callout->updateGeometry();
    }
    QGraphicsView::resizeEvent(event);
}

void Chart::mouseMoveEvent(QMouseEvent *event)
{
    m_coordX->setText(QString("X: %1").arg(m_chart->mapToValue(event->pos()).x()));
    m_coordY->setText(QString("Y: %1").arg(m_chart->mapToValue(event->pos()).y()));
    QGraphicsView::mouseMoveEvent(event);
}

void Chart::tooltip(QPointF point, bool state)
{
    if (m_chart == NULL)
        return;
    if (m_tooltip == NULL)
        m_tooltip = new Callout(m_chart);

    if (state) {
        m_tooltip->setText(QString("X: %1 \nY: %2 ").arg(point.x()).arg(point.y()));
        m_tooltip->setAnchor(point);
        m_tooltip->setZValue(11);
        m_tooltip->updateGeometry();
        m_tooltip->show();
    } else {
        m_tooltip->hide();
    }
}


void Chart::keepCallout()
{
    m_callouts.append(m_tooltip);
    m_tooltip = new Callout(m_chart);
}